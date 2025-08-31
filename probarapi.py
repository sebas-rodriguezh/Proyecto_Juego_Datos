import requests
url = "https://tigerds-api.kindflower-ccaf48b6.eastus.azurecontainerapps.io"

resp = requests.get(url+"/city/map")
data = resp.json()

print("Respuesta cruda de la API:\n")
print(data)

resp2 = requests.get(url+"/healthz")
data2 = resp2.json()

print("\nRespuesta de la API de salud:\n")
print(data2)

resp3 = requests.get(url+"/city/jobs")
data3 = resp3.json()

print("\nRespuesta de la API de trabajos:\n")
print(data3)

resp4 = requests.get(url+"/city/weather")
data4 = resp4.json()

print("\nRespuesta de la API de clima:\n")
print(data4)

