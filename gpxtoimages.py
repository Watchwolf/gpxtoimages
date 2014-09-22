# -*- coding: utf-8 -*-
import sys, os
import subprocess
import datetime, time
import argparse

gpxfile = None
output = None

parser = argparse.ArgumentParser()
parser.add_argument("-g", "--gpx", dest="gpxfile",
                  help="the input GPX file to convert into images",
                  required=True)
parser.add_argument("-o", "--output",
                  dest="outputfolder", default='./images',
                  help="the ouput folder, images will be created inside")

args = parser.parse_args()

##conversion du fichier GPX
p = subprocess.Popen(['gpsbabel', '-t', '-i', 'gpx', '-f', args.gpxfile, '-o', 'unicsv', '-x', 'track,course,speed', '-F', '/dev/stdout'], 
    stdout=subprocess.PIPE, 
    stderr=subprocess.PIPE)
out, err = p.communicate()
out = out.split('\n')
out = out[1:] ##la première ligne est l'entête (No,Latitude,Longitude,Altitude,Speed,Course,Date,Time)


##on récupère la vitesse à chaque seconde
##le GPS n'enregistre pas toute les secondes, il faut donc compléter les vides en calculant la moyenne
speeds = [] #(datetime, speed)
t1 = None
t2 = None
v1 = None
v2 = None
vmax = None
vmin = None
tmin = None
tmax = None

for line in out:
    line = line.replace('\n', '').replace('\r', '')
    split = line.split(',')
    if not len(split) == 8:
        continue

    speed = float(split[4]) * 3.6 ##conversion de la vitesse en km/h
    t = datetime.datetime.strptime('%s %s' % (split[6], split[7]) , "%Y/%m/%d %H:%M:%S")

    if not vmax or vmax < speed:
        vmax = speed
    if not vmin or vmin > speed:
        vmin = speed

    if not tmax or tmax < t:
        tmax = t
    if not tmin or tmin > t:
        tmin = t


    if not t1:
        t1 = t
        v1 = speed
        speeds.append( (t, speed) )
    else:
        t2 = t
        v2 = speed

        ##on complète les secondes manquantes
        start = int(time.mktime(t1.timetuple())) + 1
        for i in range(start, int(time.mktime(t2.timetuple()))):
            _t = t1 + datetime.timedelta(seconds=i-start+1)
            _v = (v1 + v2) / 2.
            speeds.append( (_t, _v) ) ##ici on pourrait faire une moyenne pondérer, si il manque beaucoup de secondes la moyenne simple n'est pas très précise

        speeds.append( (t2, speed) )
        t1 = t2
        t2 = None
        v1 = v2
        v2 = None


def value_formatter(value):
    return '%0.1f km/h' % value


##supressions du dossier images
os.system('mkdir -p %s' % args.outputfolder)
##


i = 0
for d, s in speeds:
    #print '%s %s' % (d, s)
    ##calcul de la couleur
    blue = (0, 255, 255)
    red = (255, 0, 0)
    diff = int( (s - vmin) * 255 / (vmax - vmin) )
    color = (0+diff, 255-diff, 255-diff)

    WIDTH = 500
    HEIGHT = 75

    SPEED_WIDTH = 500
    SPEED_HEIGHT = 75


    import cairo
    surface = cairo.ImageSurface (cairo.FORMAT_ARGB32, WIDTH, HEIGHT)
    ctx = cairo.Context (surface)

    ctx.set_source_rgba(0, 0, 0, 0.3)
    ctx.rectangle (0, 0, WIDTH, HEIGHT)
    ctx.fill()

    ctx.set_source_rgb(color[0] / 255., color[1] / 255., color[2] / 255.)
    ctx.rectangle (0, 0, int(SPEED_WIDTH * (s/vmax)), SPEED_HEIGHT)
    ctx.fill()

    ctx.set_source_rgb(1.0, 1.0, 1.0)
    ctx.select_font_face("Sans",
            cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
    ctx.set_font_size(60)
    text = '%0.1f km/h' % s
    x_bearing, y_bearing, width, height = ctx.text_extents(text)[:4]
    ctx.move_to(SPEED_WIDTH / 2 - width/2, SPEED_HEIGHT / 2 + height/2)
    ctx.show_text(text)


    ctx.stroke()
    surface.write_to_png ('%s/%5d.png' % (args.outputfolder, i))

    i += 1

