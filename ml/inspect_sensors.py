import xml.etree.ElementTree as ET

file_path = "ml/trafficSensor_tmdd.xml"

tree = ET.parse(file_path)
root = tree.getroot()

print("Root tag:", root.tag)
print("Root attributes:", root.attrib)

print()

# Find every station
stations = root.findall(
    "{http://www.openroadsconsulting.org/detector}station"
)

print("Total stations:", len(stations))

print()
print("First 10 stations:")
print("------------------")

for station in stations[:10]:

    print()

    for element in station.iter():

        tag = element.tag.split("}")[-1]

        if element.text and element.text.strip():

            print(
                f"{tag}: {element.text.strip()}"
            )