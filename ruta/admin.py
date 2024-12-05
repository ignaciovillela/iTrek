import json

from django import forms
from django.contrib import admin
from django.contrib.admin.widgets import FilteredSelectMultiple
from django.utils.safestring import mark_safe
from .models import Punto, Ruta, RutaCompartida, PuntoInteres
from user.models import Usuario


# Formulario personalizado para Punto
class PuntoForm(forms.ModelForm):
    descripcion = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'rows': 3}),
        label="Descripción del Punto de Interés"
    )
    imagen = forms.ImageField(required=False, label="Imagen del Punto de Interés")

    class Meta:
        model = Punto
        fields = ['latitud', 'longitud', 'orden']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and hasattr(self.instance, 'interes'):
            self.fields['descripcion'].initial = self.instance.interes.descripcion
            self.fields['imagen'].initial = self.instance.interes.imagen

    def save(self, commit=True):
        punto = super().save(commit=commit)
        # Asegurarse de que PuntoInteres exista
        if not hasattr(punto, 'interes'):
            PuntoInteres.objects.create(punto=punto)
        punto.interes.descripcion = self.cleaned_data['descripcion']
        punto.interes.imagen = self.cleaned_data['imagen']
        punto.interes.save()
        return punto


# Inline para Punto
class PuntoInline(admin.TabularInline):
    model = Punto
    form = PuntoForm
    extra = 0
    fields = ['latitud', 'longitud', 'orden', 'descripcion', 'imagen']

    def descripcion(self, obj):
        return obj.interes.descripcion if obj and hasattr(obj, 'interes') else None

    def imagen(self, obj):
        if obj and hasattr(obj, 'interes') and obj.interes.imagen:
            return mark_safe(f'<a href="{obj.interes.imagen.url}"><img src="{obj.interes.imagen.url}" width="100" height="100" /></a>')
        return 'No hay imagen'

    descripcion.short_description = "Descripción"
    imagen.short_description = "Imagen"


# Formulario personalizado para Ruta
class RutaForm(forms.ModelForm):
    class Meta:
        model = Ruta
        fields = '__all__'

    compartida_con = forms.ModelMultipleChoiceField(
        queryset=Usuario.objects.all(),
        required=False,
        widget=FilteredSelectMultiple('Usuarios', is_stacked=False)
    )

    class Media:
        css = {
            'all': ('admin/css/widgets.css',),
        }
        js = ('admin/js/vendor/jquery/jquery.js', 'admin/js/jquery.init.js', 'admin/js/actions.js')


# Admin de Ruta
class RutaAdmin(admin.ModelAdmin):
    inlines = [PuntoInline]
    form = RutaForm
    list_display = ('nombre', 'usuario', 'dificultad', 'creado_en')
    list_filter = ('dificultad', 'usuario')

    class Media:
        css = {
            'all': ('https://unpkg.com/leaflet@1.7.1/dist/leaflet.css',)
        }
        js = ('https://unpkg.com/leaflet@1.7.1/dist/leaflet.js',)

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        if obj and obj.puntos.exists():
            puntos_js = [
                {
                    "lat": punto.latitud,
                    "lng": punto.longitud,
                    "descripcion": punto.interes.descripcion if hasattr(punto, 'interes') else None,
                    "imagen": punto.interes.imagen.url if hasattr(punto, 'interes') and punto.interes.imagen else None
                }
                for punto in obj.puntos.all()
            ]
            puntos_js_str = json.dumps(puntos_js)
            first_punto = obj.puntos.first()

            form.base_fields['descripcion'].help_text = mark_safe(f"""
            <div id="mapid" style="height: 400px;"></div>
            <script>
                var map = L.map('mapid').setView([{first_punto.latitud}, {first_punto.longitud}], 13);
                
                L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png', {{
                    maxZoom: 18,
                    attribution: 'Map data © <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
                }}).addTo(map);
            
                var points = {puntos_js_str};
                var latlngs = [];
                points.forEach(function(p) {{
                    latlngs.push([p.lat, p.lng]);
            
                    var popupContent = "";
                    if (p.descripcion) {{
                        popupContent += "<b>Descripción:</b> " + p.descripcion;
                    }}
                    if (p.imagen) {{
                        if (popupContent !== "") {{
                            popupContent += "<br>";
                        }}
                        popupContent += '<img src="' + p.imagen + '" alt="Imagen del punto" style="max-width: 200px; max-height: 150px;">';
                    }}
            
                    if (popupContent !== "") {{
                        var marker = L.marker([p.lat, p.lng]).addTo(map);
                        marker.bindPopup(popupContent);
                    }}
                }});
            
                if (latlngs.length > 1) {{
                    var polyline = L.polyline(latlngs, {{color: 'blue'}}).addTo(map);
                    map.fitBounds(polyline.getBounds());
                }} else if (latlngs.length === 1) {{
                    map.setView(latlngs[0], 13);
                }}
            </script>
            """)
        return form


# Formulario para RutaCompartida
class RutaCompartidaForm(forms.ModelForm):
    class Meta:
        model = RutaCompartida
        fields = '__all__'

    usuario = forms.ModelChoiceField(queryset=Usuario.objects.all())
    ruta = forms.ModelChoiceField(queryset=Ruta.objects.all())


# Admin de RutaCompartida
@admin.register(RutaCompartida)
class RutaCompartidaAdmin(admin.ModelAdmin):
    form = RutaCompartidaForm
    list_display = ('ruta', 'usuario')
    search_fields = ('ruta__nombre', 'usuario__username')
    list_filter = ('ruta', 'usuario')


# Registrar Ruta
admin.site.register(Ruta, RutaAdmin)
