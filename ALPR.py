from openalpr import Alpr

alpr = Alpr("eu", "/etc/openalpr/openalpr.conf", "/etc/openalpr/runtime_data")
if not alpr.is_loaded():
    print("Erreur lors du chargement d'OpenALPR")
    exit(1)

results = alpr.recognize_file("helloworld.jpg")

for plate in results['results']:
    print("Plaque:", plate["plate"])
    print("Confiance:", plate['confidence'])

alpr.unload()
