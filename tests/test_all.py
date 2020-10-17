import unittest
import data2qr
import os

TEST_ROOT='tests'
RESOURCE='resource'
TEMP_DIR = '.tmp/'

try:
    SKIP_INTERNAL_TEST=os.environ['SKIP_INTERNAL_TEST']
except KeyError:
    SKIP_INTERNAL_TEST=0

class SingleFileTemplate(unittest.TestCase):

    def _content(self, code=False):
        with open(self._target(code), 'rb') as f:
            content = f.read()
        return content

    @classmethod
    def setup_class(cls):
        if cls is SingleFileTemplate:
            raise unittest.SkipTest('skip template test case')
        assert not os.path.exists(TEMP_DIR)

    def setup_method(self, method):
        os.makedirs(TEMP_DIR, exist_ok=False)

    def teardown_method(self, method):
        import shutil
        shutil.rmtree(TEMP_DIR)

    def test_file_exists(self):
        self.assertTrue(os.path.isfile(self._target()))

    def test_data_to_code_to_data(self):
        content = self._content()
        self.assertEqual(data2qr.code2data(data2qr.data2code(content)), content)

    def test_should_not_overwrite_existing_figure(self):
        f_name = os.path.join(TEMP_DIR, '0.png')
        assert not os.path.exists(f_name), f'test prepared fail: f_name={f_name} exists'
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
        img_names = data2qr.code2qrcode(code, prefix=TEMP_DIR)
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

class Test_EnTxt(SingleFileTemplate):

    def _target(self, code=False):
        if not code:
            return f'{TEST_ROOT}/{RESOURCE}/en_us.txt'
        else:
            return f'{TEST_ROOT}/{RESOURCE}/en_us.code'

class Test_PyCode(SingleFileTemplate):

    def _target(self, code=False):
        if not code:
            return f'{TEST_ROOT}/{RESOURCE}/py_code.txt'
        else:
            return f'{TEST_ROOT}/{RESOURCE}/py_code.code'

class Test_ZhChTxt(SingleFileTemplate):

    def _target(self, code=False):
        if not code:
            return f'{TEST_ROOT}/{RESOURCE}/zh_ch.txt'
        else:
            return f'{TEST_ROOT}/{RESOURCE}/zh_ch.code'

class Test_ZhTwTxt(SingleFileTemplate):

    def _target(self, code=False):
        if not code:
            return f'{TEST_ROOT}/{RESOURCE}/zh_ch.txt'
        else:
            return f'{TEST_ROOT}/{RESOURCE}/zh_ch.code'

class Test_JaJpTxt(SingleFileTemplate):

    def _target(self, code=False):
        if not code:
            return f'{TEST_ROOT}/{RESOURCE}/ja_jp.txt'
        else:
            return f'{TEST_ROOT}/{RESOURCE}/ja_jp.code'

class Test_TestPng(SingleFileTemplate):

    def _target(self, code=False):
        if not code:
            return f'{TEST_ROOT}/{RESOURCE}/test.png'
        else:
            return f'{TEST_ROOT}/{RESOURCE}/test_png.code'

