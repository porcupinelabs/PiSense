from distutils.core import setup

setup(
    name='PiSense',
    version='1.00',
    author='Porcupine Labs',
    author_email='info@porcupineelectronics.com',
    url='http://pypi.python.org/pypi/pisense/',
    packages=['pslog','psweb','pscmd','psmon','scanchan'],
    license='license.txt',
    description='Simple wireless sensor network for Raspberry Pi',
    long_description=open('README.md').read(),
	install_requires = ['pyserial>=2.5'],
    include_package_data = True,
	package_data = {
		'pslog': ['*.cfg','../*.txt','../*.md','../*.sh','../*.py'],
		'psweb': ['http/*.html',
                  'http/*.png',
                  'http/css/*',
                  'http/img/*.css',
                  'http/img/*.png',
                  'http/img/nodes/*',
                  'http/js/*',
                  'http/lib/*',
                  'http/partials/*'
                 ]
	}
)