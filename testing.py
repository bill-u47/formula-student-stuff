import csv
from itertools import zip_longest

carSimData = []
motecData = []
filepath = r'C:\Users\bilye\OneDrive\Desktop\formula-student-stuff\oct14CarsimSmaller.csv'
with open(filepath, 'r+', newline='') as carsimCsv:
    reader = csv.reader(carsimCsv)
    first_row = next(reader)
    for cell in first_row:
        if cell != '(null)':
            carSimData.append(cell)

with open('fb24MotecSmaller.csv', 'r+', newline='') as motecCsv:
    reader = csv.reader(motecCsv)
    for row in reader:
        if row and row[0] == 'Time':
            motecData = row

   

with open('dictionary.csv', 'w', newline='') as dictCsv:
    writer = csv.writer(dictCsv)
    carSimData.insert(0, 'CarSim Data')
    motecData.insert(0, 'Motec Data')

    for item1, item2 in zip_longest(carSimData, motecData, fillvalue=""):
        writer.writerow([item1, item2])


    notation_map = {
        'AA': 'Acceleration',
        'AV': 'Velocity',
    }

    axis_map = {
        'x': 'X direction',
        'y': 'Y direction',
        'z': 'Z direction',
    }

def interpret_notation(notation):
    type_code = notation[:2]
    axis_code = notation[2:]
    type_full = notation_map.get(type_code, 'Unknown Type')
    axis_full = axis_map.get(axis_code, 'Unknown Axis')
    return f"{type_full} in the {axis_full}"

# Batch process all your data
results = [interpret_notation(n) for n in carSimData]
print(results)

