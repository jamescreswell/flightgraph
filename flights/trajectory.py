import numpy as np

D2R = np.pi / 180.0
R2D = 180.0 / np.pi

class Coord(object):
    def __init__(self, lon, lat):
        self.lon = lon
        self.lat = lat
        self.x = D2R * lon
        self.y = D2R * lat

    def __str__(self):
        return str(self.lon) + ',' + str(self.lat)

    def antipode(self):
        anti_lat = -1.0 * self.lat
        anti_lon = 180.0 + self.lon if self.lon < 0 else 180 - self.lon
        return Coord(anti_lon, anti_lat)

class LineString(object):
    def __init__(self):
        self.coords = []
        self.length = 0

    def move_to(self, coord):
        self.length = self.length + 1
        self.coords.append(coord)

class Arc(object):
    def __init__(self, properties):
        self.properties = properties # || {}
        self.geometries = []

    def json(self):
        if len(self.geometries) <= 0:
            return {'geometry': {'type': 'LineString',
                                 'coordinates': None},
                    'type': 'Feature',
                    'properties': self.properties}
        elif len(self.geometries) == 1:
            return {'geometry': {'type': 'LineString',
                                 'coordinates': self.geometries[0].coords},
                    'type': 'Feature',
                    'properties': self.properties}
        else:
            multiline = [self.geometries[i].coords for i in range(len(self.geometries))]
            return {'geometry': {'type': 'MultiLineString',
                                 'coordinates': multiline},
                    'type': 'Feature',
                    'properties': self.properties}

    def wkt(self):
        wkt_string = ''
        wkt = 'LINESTRING('
        def collect(c):
            wkt = wkt + c[0] + ' ' + c[1] + ','
        for i in range(len(self.geometries)):
            if len(self.geometries[i].coords) == 0:
                return 'LINESTRING(empty)'
            else:
                coords = self.geometries[i].coords
                for coord in coords:
                    collect(coord)
                wkt_string = wkt_string + wkt[:len(wkt) - 1] + ')'
        return wkt_string

class GreatCircle(object):
    def __init__(self, start, end, properties):
        self.start = Coord(start['x'], start['y'])
        self.end = Coord(end['x'], end['y'])
        self.properties = properties

        w = self.start.x - self.end.x
        h = self.start.y - self.end.y
        z = np.sin(h / 2.0)**2 + np.cos(self.start.y) * np.cos(self.end.y) * np.sin(w / 2.0)**2

        self.g = 2.0 * np.arcsin(np.sqrt(z))

        if self.g == np.pi:
            print('Start and end are antipodal, good luck')
            raise ValueError()
        elif self.g == np.nan:
            print('problem')
            raise ValueError()

    def interpolate(self, f):
        A = np.sin((1.0 - f) * self.g) / np.sin(self.g)
        B = np.sin(f * self.g) / np.sin(self.g)
        x = A * np.cos(self.start.y) * np.cos(self.start.x) + B * np.cos(self.end.y) * np.cos(self.end.x)
        y = A * np.cos(self.start.y) * np.sin(self.start.x) + B * np.cos(self.end.y) * np.sin(self.end.y)
        z = A * np.sin(self.start.y) + B * np.sin(self.end.y)
        lat = R2D * np.arctan2(z, np.sqrt(x**2 + y**2))
        lon = R2D * np.arctan2(y, x)
        return [lon, lat]

    def Arc(self, npoints, options):
        first_pass = []
        if not npoints or npoints <= 2:
            first_pass.append([self.start.lon, self.start.lat])
            first_pass.append([self.end.lon, self.end.lat])
        else:
            delta = 1.0 / (npoints - 1.0)
            for i in range(npoints):
                step = delta * i
                pair = self.interpolate(step)
                first_pass.append(pair)

        bHasBigDiff = False
        dfMaxSmallDiffLong = 0.0
        dfDateLineOffset = options['offset'] if options['offset'] else 10.0
        dfLeftBorderX = 180.0 - dfDateLineOffset
        dfRightBorderX = -180.0 + dfDateLineOffset
        dfDiffSpace = 360 - dfDateLineOffset

        for j in range(len(first_pass)):
            dfPrevX = first_pass[j-1][0]
            dfX = first_pass[j][0]
            dfDiffLong = np.abs(dfX - dfPrevX)
            if dfDiffLong > dfDiffSpace and ((dfX > dfLeftBorderX and dfPrevX < dfRightBorderX) or (dfPrevX > dfLeftBorderX and dfX < dfRightBorderX)):
                bHasBigDiff = True
            elif dfDiffLong > dfMaxSmallDiffLong:
                dfMaxSmallDiffLong = dfDiffLong

        poMulti = []
        if bHasBigDiff and dfMaxSmallDiffLong < dfDateLineOffset:
            poNewLS = []
            poMulti.append(poNewLS)
            for k in range(len(first_pass)):
                dfX0 = first_pass[k][0]
                if k > 0 and np.abs(dfX0 - first_pass[k-1][0]) > dfDiffSpace:
                    dfX1 = first_pass[k-1][0]
                    dfY1 = first_pass[k-1][1]
                    dfX2 = first_pass[k][0]
                    dfY2 = first_pass[k][1]
                    if dfX1 > -180 and dfX1 < dfRightBorderX and dfX2 == 180 and k+1 < len(first_pass) and first_pass[k-1][0] > -180 and first_pass[k-1][0] < dfRightBorderX:
                        poNewLS.append([-180, first_pass[k][1]])
                        k = k + 1
                        poNewLS.append([first_pass[k][0], first_pass[k][1]])
                        # continue?
                    elif dfX1 > dfLeftBorderX and dfX1 < 180 and dfX2 == -180 and k + 1 < len(first_pass) and first_pass[k-1][0] > dfLeftBorderX and first_pass[k-1][0] < 180:
                        poNewLS.append([180, first_pass[k][1]])
                        k = k + 1
                        poNewLS.append([first_pass[k][0], first_pass[k][1]])
                        # continue

                    if dfX1 < dfRightBorderX and dfX2 > dfLeftBorderX:
                        tmpX = dfX1
                        dfX1 = dfX2
                        dfX2 = tmpX

                        tmpY = dfY1
                        dfY1 = dfY2
                        dfY2 = tmpY

                    if dfX1 > dfLeftBorderX and dfX2 < dfRightBorderX:
                        dfX2 = dfX2 + 360

                    if dfX1 <= 180 and dfX2 >= 180 and dfX1 < dfX2:
                        dfRatio = (180 - dfX1) / (dfX2 - dfX1)
                        dfY = dfRatio * dfY2 + (1 - dfRatio) * dfY1
                        poNewLs.append([180 if first_pass[k-1][0] > dfLeftBorderX else -180, dfY])
                        poNewLS = []
                        poNewLS.append([-180 if first_pass[k-1][0] > dfLeftBorderX else 180, dfY])
                        poMulti.append(poNewLS)
                    else:
                        poNewLS = []
                        poMulti.append(poNewLS)
                    poNewLS.append([dfX0, first_pass[k][1]])
                else:
                    poNewLS.append([first_pass[k][0], first_pass[k][1]])
        else:
            poNewLS0 = []
            poMulti.append(poNewLS0)
            for l in range(len(first_pass)):
                poNewLS0.append([first_pass[l][0], first_pass[l][1]])

        arc = Arc(self.properties)
        for m in range(len(poMulti)):
            line = LineString()
            arc.geometries.append(line)
            points = poMulti[m]
            for j0 in range(len(points)):
                line.move_to(points[j0])
        return arc
