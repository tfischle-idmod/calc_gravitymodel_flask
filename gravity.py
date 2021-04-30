#! /usr/bin/env python3

import json
from pathlib import Path
import numpy as np
import pycuda.driver as cuda
# import pycuda.autoinit
from pycuda.compiler import SourceModule

def get_kernel():
    kernel = SourceModule("""
        #include <cstdint>
        #include <cfloat>        

        __global__ void distance(
            uint32_t count,     // size of incoming vectors (1D) and outgoing rates (2D)
            float *lats,        // latitude of node N
            float *lons,        // longitude of node N
            float *masses,      // mass (population) of node N
            float p0,           // gravity parameter 0, p0 * (m1 ** p1) * (m2 ** p2) * (distance ** p3)
            float p1,           // gravity parameter 1
            float p2,           // gravity parameter 2
            float p3,           // gravity parameter 3
            float *distances,   // [row,col] rate from node row to node col
            float *rates        // [row,col] rate from node row to node col
        )
        {
            uint32_t x = blockIdx.x * blockDim.x + threadIdx.x;
            uint32_t y = blockIdx.y * blockDim.y + threadIdx.y;
            const double M_PI = 3.14;

            if ( (x < count) && (y < count) )
            {
                float latx = lats[x] * 3.14159265f / 180;
                float lonx = lons[x] * 3.14159265f / 180;
                float laty = lats[y] * 3.14159265f / 180;
                float lony = lons[y] * 3.14159265f / 180;

                if ( (laty != latx) || (lony != lonx) ) {

                    float popx = masses[x];
                    float popy = masses[y];

                    float a = 6378137;
                    float b = 6356752.3142;
                    float f = 1 / 298.257223563;

                    float L = lony - lonx;

                    float U1 = atan((1 - f) * tan(latx));
                    float U2 = atan((1 - f) * tan(laty));

                    float sinU1 = sin(U1);
                    float cosU1 = cos(U1);
                    float sinU2 = sin(U2);
                    float cosU2 = cos(U2);

                    float lambda = L;
                    float lambdaP = 2 * M_PI;

                    // Used in while iterations
                    float sinlambda = 0.0;
                    float coslambda = 0.0;
                    float sinsigma = 0.0;
                    float cossigma = 0.0;
                    float sinalpha = 0.0;
                    float cossqalpha = 0.0;
                    float cos2sigmam = 0.0;
                    float C = 0.0;
                    float sigma = 0.0;

                    uint32_t iterlimit = 20;

                    float result = FLT_MAX;
                    while (abs(lambda - lambdaP) > 1e-12 && --iterlimit > 0)
                    {
                        sinlambda = sin(lambda);
                        coslambda = cos(lambda);
                        sinsigma = sqrt((cosU2 * sinlambda) * (cosU2 * sinlambda) + (cosU1 * sinU2 - sinU1 * cosU2 * coslambda) * (cosU1 * sinU2 - sinU1 * cosU2 * coslambda));
                        if (sinsigma == 0) {
                            result = 0.0f;
                            break; //co-incident points
                        }
                        cossigma = sinU1 * sinU2 + cosU1 * cosU2 * coslambda;
                        sigma = atan2(sinsigma, cossigma);
                        sinalpha = cosU1 * cosU2 * sinlambda / sinsigma;
                        cossqalpha = 1 - sinalpha * sinalpha;
                        cos2sigmam = cossigma - 2 * sinU1 * sinU2 / cossqalpha;
                        if (isnan(cos2sigmam)) cos2sigmam = 0; //equatorial line: cossqalpha=0
                        C = f / 16 * cossqalpha * (4 + f * (4 - 3 * cossqalpha));
                        lambdaP = lambda;
                        lambda = L + (1 - C) * f * sinalpha * (sigma + C * sinsigma * (cos2sigmam + C * cossigma * (-1 + 2 * cos2sigmam * cos2sigmam)));
                    }

                    if (iterlimit > 0)
                    {
                        if (result != 0.0f)
                        {
                            float uSq = cossqalpha * (a * a - b * b) / (b * b);
                            float A = 1 + uSq / 16384 * (4096 + uSq * (-768 + uSq * (320 - 175 * uSq)));
                            float B = uSq / 1024 * (256 + uSq * (-128 + uSq * (74 - 47 * uSq)));
                            float deltasigma = B * sinsigma * (cos2sigmam + B / 4 * (cossigma * (-1 + 2 * cos2sigmam * cos2sigmam) - B / 6 * cos2sigmam * (-3 + 4 * sinsigma * sinsigma) * (-3 + 4 * cos2sigmam * cos2sigmam)));
                            float s = b * A * (sigma - deltasigma);

                            result = float(s / 1000);
                        }
                    }
                    else
                    {
                        result = float(nan(""));
                    }

                    float dist = result;
                    distances[y * count + x] = dist;
                    float rate = (dist != 0.0f) ? p0 * powf(popx, p1) * powf(popy, p2) * powf(dist, p3) : 0.0f;
                    rates[y * count + x] = rate;

                    // printf(\"Calculating %d (%f,%f:%d) -> %d (%f, %f:%d) = %f (%f)\\n\", x, latx, lonx, int(popx), y, laty, lony, int(popy), dist, rate);
                }
                else
                {
                    // printf(\"Nodes %d and %d have the same lat/long.\\n\", x, y);
                    distances[y * count + x] = 0.0f;
                    rates[y * count + x] = 0.0f;
                }
            }

            return;
        }
    """)

    kernel_fn = kernel.get_function("distance")

    return kernel_fn


def from_json(filename: Path, out_path: Path, parameters: dict) -> Path:

    with filename.open("rt") as input:
        jason = json.load(input)

    nodes = jason["Nodes"]

    # Consider filtering out any nodes missing Latitude or Longitude

    default_pop = get_default_population(jason)

    lat = np.asarray([node["NodeAttributes"]["Latitude"] for node in nodes], dtype=np.float32)
    lon = np.asarray([node["NodeAttributes"]["Longitude"] for node in nodes], dtype=np.float32)
    pop = np.asarray([get_node_population(node, default_pop) for node in nodes], dtype=np.float32)

    distances, rates = calculate_rates(lat, lon, pop, parameters)

    #output = Path(__file__).parent.absolute() / "results" / (filename.stem + ".npy")
    output = Path(out_path, filename.stem + ".npy")
    np.save(output, rates)

    return output


def get_default_population(jason: dict) -> int:
    if "Defaults" in jason:
        if "NodeAttributes" in jason["Defaults"]:
            if "InitialPopulation" in jason["Defaults"]["NodeAttributes"]:
                return jason["Defaults"]["NodeAttributes"]["InitialPopulation"]

    return 0


def get_node_population(node: dict, default: int) -> int:
    return node["NodeAttributes"]["InitialPopulation"] if "InitialPopulation" in node["NodeAttributes"] else default


def calculate_rates(lat: np.ndarray, lon: np.ndarray, pop: np.ndarray, parameters: dict) -> tuple:

    cuda.init()
    device = cuda.Device(0)
    context = device.make_context()
    kernel_fn = get_kernel()

    p0 = float(parameters["p0"]) if "p0" in parameters else 1.0
    p1 = float(parameters["p1"]) if "p1" in parameters else 1.0
    p2 = float(parameters["p2"]) if "p2" in parameters else 1.0
    p3 = float(parameters["p3"]) if "p3" in parameters else -2.0

    count = len(lat)
    distances = np.zeros((count, count), dtype=np.float32)
    rates = np.zeros((count, count), dtype=np.float32)

    BLOCK_DIM = 32
    GRID_DIM = (count + BLOCK_DIM - 1) // BLOCK_DIM
    try:
        kernel_fn(np.uint32(count),
                cuda.In(lat), cuda.In(lon), cuda.In(pop),
                np.float32(p0), np.float32(p1), np.float32(p2), np.float32(p3),
                cuda.Out(distances), cuda.Out(rates),
                block=(BLOCK_DIM, BLOCK_DIM, 1), grid=(GRID_DIM, GRID_DIM))
    finally:
        context.pop()

    return distances, rates
