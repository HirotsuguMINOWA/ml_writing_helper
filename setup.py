from setuptools import setup, find_packages


with open('requirements.txt') as requirements_file:
    install_requirements = requirements_file.read().splitlines()

setup(
    name="conv_doc",
    version="0.0.1",
    description="A small package",
    author="Hirotsugu Minowa",
    packages=find_packages(),
    install_requires=install_requirements,
    # 要検討
    # もしCLIツールを作る場合は、下記通りentrypointを指定するとよい。
    # 実行した下位Folderすべて監視して、pptxをpngに変換してはどうか
    #
    # entry_points={
    #     "console_scripts": [
    #         "conv_luxuary=ml_writing_helper.watcher_pptx2pdf:main",
    #     ]
    # },
    classifiers=[
        'Programming Language :: Python :: 3.6',
    ]
)