# Docker UI for a Private Registry

The following code will create a Flask app that that displays a graph of submission frequency, then a table of the submissions themselves to the private Docker repository.

The table makes calls to the API to pull out metadata such as last modified timestamps and tag information.

The app has a hardcoded Docker registry url at the beginning that will need to be customized. 

## Next Steps

1. Moving the Docker registry url to an argument value could be beneficial to some users.

2. Moving data called from the Docker registry API to a database that would speed up the generation process.