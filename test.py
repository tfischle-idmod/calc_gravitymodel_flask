import unittest
import server
import pathlib

class MyTestCase(unittest.TestCase):
    @classmethod
    def setUp(self):
        self.app = server.app.test_client()  # run(debug=True, host='127.0.0.1', port=3135)
        self.server_url = 'http://localhost:3135'

    def test_file_uploaded_and_created_with_uuid(self):
        dictToSend = {'file': open("demographics.json", "rb")}
        response = self.app.post(self.server_url + '/uploader', data=dictToSend)
        print("response from server:", response.data)

        self.assertEqual(response.status_code, 200)
        path_created_file = pathlib.Path('uploads', response.data.decode())
        self.assertTrue(path_created_file.is_file())

if __name__ == '__main__':
    unittest.main()
