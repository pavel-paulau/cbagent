clean: ; \
    rm -f `find . -name *.pyc`; \
    rm -fr cbagent.egg-info dist; \
    rm -f .coverage

test: ; \
    nosetests --with-coverage --cover-package=cbagent
