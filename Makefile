all: publish

clean:
	rm -rf dist pepa.egg-info

publish: clean
	python setup.py sdist
	twine upload dist/*

