import unittest
import data2qr
import os

TEST_ROOT='tests'
RESOURCE='resource'

try:
    SKIP_INTERNAL_TEST=os.environ['SKIP_INTERNAL_TEST']
except KeyError:
    SKIP_INTERNAL_TEST=0

class Test_EnTxt(unittest.TestCase):

    def _target(self, code=False):
        if not code:
            return f'{TEST_ROOT}/{RESOURCE}/en_txt'
        else:
            return f'{TEST_ROOT}/{RESOURCE}/en_txt.code'

    def _content(self, code=False):
        with open(self._target(code), 'r') as f:
            content = f.read()
        return content

    def test_file_exists(self):
        self.assertTrue(os.path.isfile(self._target()))

    def test_data_to_code_to_data(self):
        content = self._content()
        self.assertEqual(data2qr.code2data(data2qr.data2code(content)), content)

    def test_should_not_overwrite_existing_figure(self):
        f_name = '0.png'
        self.assertFalse(os.path.exists(f_name))
        with open(f_name, 'w') as f:
            f.write('test')
        content = self._content()
        code = data2qr.data2code(content)
        with self.assertRaises(os.error) as context:
            try:
                data2qr.code2qrcode(code, [f_name])
            except Exception as e:
                raise e
            finally:
                os.remove(f_name)
        self.assertEqual(f'File "{f_name}" exists', str(context.exception))

    def test_data_to_qrcode_to_data(self):
        content = self._content()
        code = data2qr.data2code(content)
        img_names = data2qr.code2qrcode(code)
        codes = []
        for img_name in img_names:
            codes.append(data2qr.qrcode2code(img_name))
            os.remove(img_name)
        self.assertEqual(data2qr.code2data(''.join(codes)), content)

    @unittest.expectedFailure
    def test_data_to_code_to_different_data(self):
        content = self._content()
        self.assertEqual(data2qr.code2data(data2qr.data2code(content)), content + 'HELLO')

    @unittest.skipUnless(SKIP_INTERNAL_TEST==0, 'skipping internal test')
    def test_data_to_code(self):
        content = self._content()
        code = self._content(code=True)
        self.assertEqual(data2qr.data2code(content), code)

    @unittest.skipUnless(SKIP_INTERNAL_TEST==0, 'skipping internal test')
    def test_code_to_data(self):
        content = self._content()
        code = self._content(code=True)
        self.assertEqual(data2qr.code2data(code), content)

class Test_PyCode(Test_EnTxt):

    def _target(self, code=False):
        if not code:
            return f'{TEST_ROOT}/{RESOURCE}/py_code'
        else:
            return f'{TEST_ROOT}/{RESOURCE}/py_code.code'

