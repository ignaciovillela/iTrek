from django.db import migrations


def create_ruta_san_cristobal(apps, schema):
    Ruta = apps.get_model('ruta.Ruta')
    Punto = apps.get_model('ruta.Punto')

    ruta = Ruta.objects.create(
        nombre="Ruta por el Cerro San Cristóbal",
        descripcion="Ruta desde la entrada principal del Parque Metropolitano hasta la cumbre del Cerro San Cristóbal.",
        dificultad="moderada",
        distancia_km=5.0,
        tiempo_estimado_horas=2.0
    )

    puntos = [
        {"latitud": -33.41528, "longitud": -70.61755, "orden": 1},
        {"latitud": -33.41631, "longitud": -70.61934, "orden": 2},
        {"latitud": -33.41403, "longitud": -70.61795, "orden": 3},
        {"latitud": -33.41321, "longitud": -70.61636, "orden": 4},
        {"latitud": -33.41367, "longitud": -70.61463, "orden": 5},
        {"latitud": -33.41298, "longitud": -70.61577, "orden": 6},
        {"latitud": -33.41398, "longitud": -70.62140, "orden": 7},
        {"latitud": -33.41528, "longitud": -70.62093, "orden": 8},
        {"latitud": -33.41617, "longitud": -70.62295, "orden": 9},
        {"latitud": -33.41746, "longitud": -70.62552, "orden": 10},
        {"latitud": -33.41817, "longitud": -70.62879, "orden": 11},
        {"latitud": -33.41845, "longitud": -70.62541, "orden": 12},
        {"latitud": -33.42178, "longitud": -70.62720, "orden": 13},
        {"latitud": -33.42223, "longitud": -70.63047, "orden": 14},
        {"latitud": -33.42280, "longitud": -70.63147, "orden": 15},
        {"latitud": -33.42395, "longitud": -70.63241, "orden": 16},
        {"latitud": -33.42586, "longitud": -70.63223, "orden": 17},
        {"latitud": -33.42644, "longitud": -70.63294, "orden": 18}
    ]

    for punto in puntos:
        Punto.objects.create(
            ruta=ruta,
            latitud=punto['latitud'],
            longitud=punto['longitud'],
            orden=punto['orden']
        )


def delete_ruta_san_cristobal(apps, schema_editor):
    Ruta = apps.get_model('ruta.Ruta')
    Punto = apps.get_model('ruta.Punto')

    ruta = Ruta.objects.filter(nombre="Ruta por el Cerro San Cristóbal").first()

    if ruta:
        Punto.objects.filter(ruta=ruta).delete()
        ruta.delete()


class Migration(migrations.Migration):

    dependencies = [
        ('ruta', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(
            create_ruta_san_cristobal,
            delete_ruta_san_cristobal,
        ),
    ]
