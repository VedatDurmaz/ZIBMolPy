#http://ghantoos.org/2008/10/19/creating-a-deb-package-from-a-python-setuppy/#comment-252

all:
	@echo "make install - Install on local system"
	@echo "make install-home - Install for this user"
	@echo "make clean - Get rid of scratch and byte files"
	@echo "make docu - Generate API documentation"
	@echo "make upload-docu - Upload API-docu to webserver"
	@echo "make todo - Show all TODOs"
	@echo "make pylint - Run pylint"

docu:
#	use python-modules from source - not the ones installed on the system
	@export PYTHONPATH=./ZIBMolPy_package/:$(PYTHONPATH); epydoc --conf=./scripts/epydoc.conf

upload-docu:
	./scripts/upload_docu.sh	

install-home:
	./scripts/installer.py --prefix=$(HOME) install
	
install:
	./scripts/installer.py install

clean:
	rm -rvf ZIBMolPy_package/build
	rm -rvf ./apidocs

todo:
	grep --color -r --exclude-dir="build" --exclude-dir=".*" --include="*.py" "TODO" *

pylint:
	cd tools; pylint --rcfile=../scripts/pylintrc `find ../ZIBMolPy_package/ZIBMolPy/ -name \*.py` ./zgf_*.py 

	
.PHONY: all docu upload-docu install install-home clean todo pylint 
#EOF
