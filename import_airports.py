# Import airport data from open source CSVs at http://ourairports.com/data/
# To be called from inside manage.py shell
import csv
from flights.models import Airport

def get_regions():
    regions = {}
    with open('/home/james/Desktop/regions.csv', newline='') as csvfile:
        reader = csv.reader(csvfile, delimiter=',')
        for row in reader:
            regions[row[1]] = row[3]
    return regions

def get_countries():
    countries = {}
    with open('/home/james/Desktop/countries.csv', newline='') as csvfile:
        reader = csv.reader(csvfile, delimiter=',')
        for row in reader:
            countries[row[1]] = row[2]
    return countries
        
def get_elevation(datum):
    if datum == '':
        return 0.0
    else:
        return datum

def import_all():
    countries = get_countries()
    regions = get_regions()
    with open('/home/james/Desktop/airports.csv', newline='') as csvfile:
        reader = csv.reader(csvfile, delimiter=',')
        for row in reader:
            if row[11] == 'yes':
                a = Airport(iata = row[13],
                            icao = row[1],
                            name = row[3],
                            city = row[10],
                            region = regions[row[9]],
                            region_iso = row[9],
                            country = countries[row[8]],
                            country_iso = row[8],
                            latitude = float(row[4]),
                            longitude = float(row[5]),
                            elevation = get_elevation(row[6]))
                
                a.save()