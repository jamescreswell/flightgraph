from flights.models import Airport, Flight
from django.contrib.auth.models import User

import csv


if '__name__' != '__main__':
    filename = 'ST_CIC.txt'
    print('test')

    with open(filename, 'r') as f:
        reader = csv.reader(f, delimiter=' ', skipinitialspace=True)
        flist = list(reader)

    # flist[5] = ['SAT', '22SEP84', 'LHR-CDG', 'BA302', '757', 'CLUB', '188', '2010']






    sortid = 0
    acct = User.objects.get(username='cicreswell')

    DATA = {}
    DATA['months'] = {'JAN': 1,
                      'FEB': 2,
                      'MAR': 3,
                      'APR': 4,
                      'MAY': 5,
                      'JUN': 6,
                      'JUL': 7,
                      'AUG': 8,
                      'SEP': 9,
                      'OCT': 10,
                      'NOV': 11,
                      'DEC': 12}


    DATA['airlines'] = {'AA': 'American Airlines',
                        'BA': 'British Airways',
                        'SK': 'Scandinavian Airlines',
                        'U2': 'EasyJet',
                        'UA': 'United Airlines',
                        'DL': 'Delta Air Lines',
                        'TK': 'Turkish Airlines',
                        'LH': 'Lufthansa',
                        'OS': 'Austrian Airlines',
                        'LO': 'LOT Polish Airlines',
                        'FI': 'Icelandair',
                        'OU': 'Croatia Airlines',
                        'LX': 'Swiss',
                        'EI': 'Aer Lingus',
                        'BE': 'FlyBe',
                        'CZ': 'China Southern',
                        'EY': 'Etihad',
                        'AZ': 'Alitalia',
                        'US': 'US Airways',
                        'LM': 'Loganair',
                        'QF': 'Qantas',
                        'KL': 'KLM',
                        'EK': 'Emirates',
                        'AF': 'Air France',
                        'VS': 'Virgin Atlantic',
                        'BR': 'British Caledonian',
                        'BD': 'British Midland',
                        'OA': 'Olympic Airways',
                        'IB': 'Iberia',
                        'SR': 'Swisair',
                        'DH': 'x',
                        'x': 'x',
                        'NA': 'Air Calédonie',
                        'LI': 'LIAT',
                        'OG': 'Air Guadeloupe',
                        'SA': 'South African Airways',
                        'SN': 'Brussels Airlines',
                        'LA': 'LAN Airlines',
                        'HA': 'Hawaiian Airlines',
                        'AQ': 'Aloha Airlines',
                        'AC': 'Air Canada',
                        'AY': 'Finnair',
                        'NZ': 'Air New Zealand',
                        'TF': 'Malmo Aviation',
                        'WN': 'Southwest',
                        'TG': 'Thai Airways',
                        'KE': 'Korean Air',
                        'H3': 'Harbour Air',
                        }
    DATA['planes'] = {'737': 'Boeing 737',
                      '727': 'Boeing 727',
                      '747': 'Boeing 747',
                      '757': 'Boeing 757',
                      '767': 'Boeing 767',
                      '777': 'Boeing 777',
                      '787': 'Boeing 787',
                      'DC10': 'McDonnell Douglas DC-10',
                      'MD80': 'McDonnell Douglas MD-80',
                      'AB300': 'Airbus A300',
                      'AB320': 'Airbus A320',
                      'AB319': 'Airbus A319',
                      'AB321': 'Airbus A321',
                      'AB330': 'Airbus A330',
                      'AB340': 'Airbus A340',
                      'EM190': 'Embraer E-190',
                      'EM175': 'Embraer E-175',
                      'EM170': 'Embraer E-170',
                      'EM145': 'Embraer ERJ-145',
                      'EM140': 'Embraer ERJ-140',
                      'EM135': 'Embraer ERJ-135',
                      'CRJ700': 'Bombardier CRJ-700',
                      'CRJ900': 'Bombardier CRJ-900',
                      'CRJ200': 'Bombardier CRJ-200',
                      'DC9': 'McDonnell Douglas DC-9',
                      'TRISTAR': 'Lockheed L-1011 TriStar',
                      'AB310': 'Airbus A310',
                      'CONCORDE': 'Concorde',}

    for row in flist[1:]:
        if row != []:
            date_string = row[1]
            if len(date_string) == 6:
                date_string = "0"  + date_string
            day = int(date_string[:2])
            month_string = date_string[2:5]
            year_suffix = int(date_string[5:])
            if int(year_suffix) > 18:
                year = 1900 + year_suffix
            else:
                year = 2000 + year_suffix
            month = DATA['months'][month_string]

            origin_iata = row[2][:3]
            destination_iata = row[2][4:]

            origin = Airport.objects.get(iata=origin_iata)
            destination = Airport.objects.get(iata=destination_iata)

            flight_number = row[3]

            airline = DATA['airlines'][flight_number[:2]]

            plane = row[4]
            if plane in DATA['planes']:
                plane = DATA['planes'][plane]

            registration = row[5]

            f = Flight(date = str(year) + '-' + str(month) + '-' + str(day),
                       number = flight_number,
                       origin=origin,
                       destination=destination,
                       airline = airline,
                       aircraft = plane,
                       aircraft_registration = registration,
                       owner=acct,
                       sortid=sortid)
            f.save()

            sortid = sortid + 2







    # date_string = date[:4] + '-' + date[4:6] + '-' + date[6:]
    # number = flight[1]
    # airports = flight[2]
    #
    # origin_code = airports[:3]
    # destination_code = airports[4:]
    #
    # try:
    #     if origin_code == 'Pe1':
    #         origin = Airport.objects.get(pk=4002)
    #     elif origin_code == 'Lo1':
    #         origin = Airport.objects.get(pk=4004)
    #     elif origin_code == 'Se1':
    #         origin = Airport.objects.get(pk=4003)
    #     else:
    #         origin = Airport.objects.get(iata=origin_code)
    #
    #     if destination_code == 'Pe1':
    #         destination = Airport.objects.get(pk=4002)
    #     elif origin_code == 'Lo1':
    #         destination = Airport.objects.get(pk=4004)
    #     elif origin_code == 'Se1':
    #         destination = Airport.objects.get(pk=4003)
    #     else:
    #         destination = Airport.objects.get(iata=destination_code)
    #     airline = flight[3]
    #     aircraft = flight[4]
    #     aircraft_reg = flight[5]
    #     f = Flight(date = date_string,
    #                number = number,
    #                origin=origin,
    #                destination=destination,
    #                airline = airline,
    #                aircraft = aircraft,
    #                aircraft_registration = aircraft_reg,
    #                owner=him,
    #                sortid=sortid)
    #     f.save()
    # except:
    #     print(date_string, number, origin, destination, airline, aircraft, aircraft_reg, him, sortid)
    # sortid = sortid + 1
