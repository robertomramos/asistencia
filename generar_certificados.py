#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
════════════════════════════════════════════════════════════════
 GENERADOR DE CERTIFICADOS · OAD 2026
 Carrera Contaduría Pública · UMSA
════════════════════════════════════════════════════════════════

 QUÉ PRODUCE
 -----------
 1. certificados-IMPRENTA.pdf   Un solo archivo, todas las páginas.
                                Sin firmas ni sellos: las autoridades
                                firman sobre el papel.
 2. certificados.js             El registro que lee verificar.html en
                                GitHub Pages. Sin esto los QR no validan.

 CÓMO USARLO
 -----------
   pip install qrcode pillow pypdf
   # Y wkhtmltopdf desde https://wkhtmltopdf.org/downloads.html

   python3 generar_certificados.py Certificados.csv

 Las tipografías van en la carpeta ./fuentes y se cargan solas:
 no hace falta instalar nada en el sistema.

 El CSV sale de: menú OAD ▸ Exportar para certificados,
 y luego Archivo ▸ Descargar ▸ CSV.

════════════════════════════════════════════════════════════════
"""

import csv, os, sys, json, base64, subprocess, shutil, tempfile, re


def buscar_wkhtmltopdf():
    """
    Busca el programa. Si no está en el PATH, prueba las carpetas
    donde el instalador de Windows lo deja por defecto.
    """
    ruta = shutil.which('wkhtmltopdf')
    if ruta:
        return ruta
    candidatos = [
        r'C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe',
        r'C:\Program Files (x86)\wkhtmltopdf\bin\wkhtmltopdf.exe',
        '/usr/local/bin/wkhtmltopdf', '/usr/bin/wkhtmltopdf',
        '/opt/homebrew/bin/wkhtmltopdf',
    ]
    for c in candidatos:
        if os.path.exists(c):
            return c
    return None


WK = buscar_wkhtmltopdf()

# Alto del lienzo en píxeles. Cada versión de wkhtmltopdf corta la
# página en un punto distinto: si es muy alto el certificado se parte
# en dos hojas, si es muy bajo queda una franja blanca en el borde.
# calibrar_alto() encuentra el valor exacto de esta computadora.
# 1062 es el ancho de lienzo que llena el papel de borde a borde.
# Con menos, wkhtmltopdf deja una franja blanca al costado; el valor
# no depende del tamaño de papel, sino del renderizador.
ANCHO = 1062
PAPEL = {'Letter': 279.4/215.9, 'A4': 297.0/210.0, 'Legal': 355.6/215.9}
ALTO = 1374


def contar_paginas(pdf):
    try:
        from pypdf import PdfReader
        return len(PdfReader(pdf).pages)
    except ImportError:
        pass
    try:
        out = subprocess.run(['pdfinfo', pdf], capture_output=True, text=True).stdout
        for l in out.splitlines():
            if l.startswith('Pages:'):
                return int(l.split()[1])
    except Exception:
        pass
    return 1


def calibrar_alto(muestra, REC):
    """
    Renderiza una página de prueba con distintos altos y se queda con
    el mayor que siga cabiendo en UNA sola hoja. Así el certificado
    llena el papel sin partirse, en cualquier versión del programa.
    """
    global ALTO
    tmp = tempfile.mkdtemp(prefix='calib_')
    try:
        techo = int(ANCHO * PAPEL.get(CFG['papel'], 1.4143) * 1.045)
        piso  = int(techo * 0.92)
        for h in range(techo, piso, -5):
            ALTO = h
            ruta_h = os.path.join(tmp, 'c.html')
            ruta_p = os.path.join(tmp, 'c.pdf')
            with open(ruta_h, 'w', encoding='utf-8') as f:
                f.write(construir_html(muestra, REC, False))
            subprocess.run([WK, '--enable-local-file-access', '--page-size', CFG['papel'],
                            '-T','0','-B','0','-L','0','-R','0','-q', ruta_h, ruta_p],
                           check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            if contar_paginas(ruta_p) == 1:
                print('   alto calibrado: %d px' % h)
                return h
        ALTO = 1400
        print('   no se pudo calibrar; se usa 1400 px')
        return ALTO
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

# ─────────────────────────────────────────────────────────────
#  CONFIGURACIÓN · edita aquí lo que cambie
# ─────────────────────────────────────────────────────────────

CFG = {
    'evento':      'Conferencias Magistrales 2026',
    'aniversario': '56° Aniversario de la Carrera Contaduría Pública',
    'fechas':      'del 24 al 28 de agosto de 2026',
    'fechas_corta':'24 al 28 de agosto de 2026',
    'resolucion':  '1028/2026',      # Resolución HCF de 18 de agosto de 2026
    'horas':       40,
    'lugar_fecha': 'La Paz, septiembre de 2026',

    # Dirección donde vive verificar.html. El QR apunta aquí.
    'base_verificacion': 'https://robertomramos.github.io/asistencia/',

    'director':  ('M. Sc. N. René Mejía Flores',
                  'DIRECTOR', 'CARRERA CONTADURÍA PÚBLICA'),
    'decano':    ('M. Sc. Boris Leandro Quevedo Calderón',
                  'DECANO', 'FACULTAD DE CIENCIAS ECONÓMICAS Y FINANCIERAS'),

    # Tamaño de papel. 'Letter' es el tamaño carta (216 x 279 mm),
    # el que usan las imprentas en Bolivia. 'A4' es 210 x 297 mm.
    'papel':     'Letter',

    'recursos':  '.',      # carpeta con los PNG de logos, firmas y sellos
    'salida':    'salida',
}

# Las 23 conferencias. El CSV trae los códigos (G1C1, G2C3…) y de
# aquí se arma el texto. Si cambia el cronograma, se corrige acá.
CONFS = {
 'G1C1': ('Mg.Sc. Gonzalo Terán Gandarillas','Tratamiento contable: Impuesto sobre las Utilidades, Impuesto a las Transacciones, Impuesto al Valor Agregado y retiros personales de socios','Martes 25','09:00 – 12:00'),
 'G1C2': ('Mg.Sc. Edwin Gutiérrez Zapana','Ajustes y regularizaciones contables al cierre del ejercicio','Miércoles 26','09:00 – 10:20'),
 'G1C3': ('Mg.Sc. N. René Mejía Flores','Gestión y Control Financiero mediante la Conciliación Bancaria','Miércoles 26','10:40 – 12:00'),
 'G1C4': ('Mg.Sc. Ausberto Choque Mita','Combinación de negocios','Jueves 27','09:00 – 10:20'),
 'G1C5': ('Ph.D. Luis E. Hinojosa Rodríguez','Planificación Financiera: el presupuesto como herramienta estratégica para la toma de decisiones','Jueves 27','10:40 – 12:00'),
 'G1C6': ('Mg.Sc. Teddy O. Catalán Mollinedo','La importancia de la aplicación de la norma tributaria en la determinación del IUE','Viernes 28','09:00 – 10:20'),
 'G1C7': ('Mg.Sc. Rolando Marín Ibáñez','La importancia de la Microeconomía y Macroeconomía para entender la coyuntura económica en Bolivia','Viernes 28','10:40 – 12:00'),

 'G2C1': ('Mg.Sc. Ronny Yáñez Mendoza','Costos ABC/ABM basado en negocios, costos basados en actividades','Lunes 24','17:30 – 18:50'),
 'G2C2': ('Mg.Sc. Vicente W. Aguirre Tarquino','Análisis del gasto público a través de la ejecución presupuestaria','Lunes 24','19:10 – 20:30'),
 'G2C3': ('Mg.Sc. Alvaro Alurralde Molina','El riesgo empresarial que no aparece en los Estados Financieros','Martes 25','17:30 – 18:50'),
 'G2C4': ('Mg.Sc. Rubén Centellas España','El apocalipsis contable','Martes 25','19:10 – 20:30'),
 'G2C5': ('Ph.D. Freddy Huanca Mamani','Compatibilidad del software contable para el envío de Estados Financieros en el SIAT','Jueves 27','17:30 – 18:50'),
 'G2C6': ('Mg.Sc. Jesús C. Gómez Revilla','El Buen Gobierno Corporativo','Jueves 27','19:10 – 20:30'),
 'G2C7': ('Mg.Sc. Rolando J. Magne Singuri','Origen, evolución y actualidad de los PCGA, Normas de Contabilidad, NIIF completas, NIIF para las PYMES y FASB','Viernes 28','17:30 – 18:50'),
 'G2C8': ('Lic. Anghelo J. Saravia Alberto','El derecho tributario desde la corrupción pública','Viernes 28','19:10 – 20:30'),

 'G3C1': ('Mg.Sc. Edwin R. Burgos Fernández','Cuando llega la fiscalización: el poder del respaldo documental en la Contabilidad','Lunes 24','17:30 – 18:50'),
 'G3C2': ('Mg.Sc. David Valdivia Peralta','Tipo de Cambio Flexible y Hechos Posteriores','Lunes 24','19:10 – 20:30'),
 'G3C3': ('Mg.Sc. Juan C. Lea Plaza López','Inteligencia artificial en auditoría interna','Martes 25','17:30 – 18:50'),
 'G3C4': ('Mg.Sc. Edgar W. Tudela Cornejo','Cómo la IA está transformando el proceso de las auditorías y la detección de fraude en Bolivia','Martes 25','19:10 – 20:30'),
 'G3C5': ('Mg.Sc. Milton M. Chávez Arias','Riesgos emergentes y su impacto en la auditoría','Jueves 27','17:30 – 18:50'),
 'G3C6': ('Mg.Sc. Carlos R. Coronel Tapia','El perfil del defraudador y los distintos tipos de fraude','Jueves 27','19:10 – 20:30'),
 'G3C7': ('Mg.Sc. Humberto Quintanilla Muñoz','La Modelación Financiera Profesional','Viernes 28','17:30 – 18:50'),
 'G3C8': ('Mg.Sc. Guido R. Yujra Segales','El rol de las Unidades de Auditoría Interna en las Empresas Públicas','Viernes 28','19:10 – 20:30'),
}

ORDEN = list(CONFS.keys())   # el índice que usa certificados.js


# ─────────────────────────────────────────────────────────────
#  UTILIDADES
# ─────────────────────────────────────────────────────────────

def b64(ruta):
    """Incrusta una imagen en el HTML: evita rutas rotas al renderizar."""
    if not os.path.exists(ruta):
        return ''
    ext = 'svg+xml' if ruta.endswith('.svg') else 'png'
    with open(ruta, 'rb') as f:
        return 'data:image/%s;base64,%s' % (ext, base64.b64encode(f.read()).decode())


def qr_b64(texto):
    import qrcode
    from io import BytesIO
    q = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_M,
                      box_size=10, border=0)
    q.add_data(texto); q.make(fit=True)
    buf = BytesIO()
    q.make_image(fill_color='black', back_color='white').save(buf, format='PNG')
    return 'data:image/png;base64,' + base64.b64encode(buf.getvalue()).decode()


def agrupar_por_dia(codigos):
    """Devuelve [(día, [(tema, expositor), …]), …] en orden cronológico."""
    orden_dia = ['Lunes 24','Martes 25','Miércoles 26','Jueves 27','Viernes 28']
    dias = {}
    for cod in codigos:
        if cod not in CONFS: continue
        exp, tema, dia, hora = CONFS[cod]
        dias.setdefault(dia, []).append((tema, exp, hora))
    salida = []
    for d in orden_dia:
        if d in dias:
            salida.append((d, sorted(dias[d], key=lambda x: x[2])))
    return salida


def escapar(t):
    return (str(t).replace('&','&amp;').replace('<','&lt;').replace('>','&gt;'))


def tam_nombre(nombre):
    """Ajusta el cuerpo del nombre para que nunca desborde su línea."""
    n = len(nombre)
    if n <= 22: return 76
    if n <= 27: return 68
    if n <= 32: return 60
    if n <= 38: return 53
    if n <= 44: return 47
    if n <= 52: return 42
    return 38


# ─────────────────────────────────────────────────────────────
#  PLANTILLA
# ─────────────────────────────────────────────────────────────

def bloque_fuentes():
    """
    Incrusta las tipografías desde ./fuentes. Así el certificado sale
    idéntico en cualquier computadora, sin instalar nada en el sistema.
    """
    ruta = os.path.abspath(os.path.join(CFG['recursos'], 'fuentes'))
    if not os.path.isdir(ruta):
        return ''
    def url(n):
        p = os.path.join(ruta, n).replace('\\', '/')
        return 'file:///' + p.lstrip('/')
    reglas = []
    # Un archivo por peso: las tipografías variables no funcionan
    # en el motor de wkhtmltopdf.
    for fam, arch, peso in [
        ('Great Vibes','GreatVibes.ttf',            400),
        ('Cinzel',     'Cinzel-Regular.ttf',        400),
        ('Cinzel',     'Cinzel-Bold.ttf',           700),
        ('Cormorant',  'Cormorant-Regular.ttf',     400),
        ('Cormorant',  'Cormorant-SemiBold.ttf',    600),
        ('Montserrat', 'Montserrat-Regular.ttf',    400),
        ('Montserrat', 'Montserrat-Medium.ttf',     500),
        ('Montserrat', 'Montserrat-SemiBold.ttf',   600),
        ('Montserrat', 'Montserrat-Bold.ttf',       700),
    ]:
        if not os.path.exists(os.path.join(ruta, arch)):
            continue
        reglas.append("@font-face{font-family:'%s';font-weight:%d;font-style:normal;"
                      "src:url('%s') format('truetype')}" % (fam, peso, url(arch)))
    return '\n'.join(reglas) + '\n'


def construir_css(REC, aire=4):
    return (bloque_fuentes() + """
@page{margin:0}
*{box-sizing:border-box;margin:0;padding:0}
html,body{width:__ANCHO__px;height:__ALTO__px;overflow:hidden;max-width:__ANCHO__px}
body{font-family:"Montserrat","DejaVu Sans",sans-serif;color:#16202E;position:relative;
  overflow:hidden;background:#fff}

.marco{position:absolute;top:26px;left:26px;right:26px;bottom:26px;
  border:2.5px solid #C9982A;z-index:4}
.marco:after{content:"";position:absolute;top:7px;left:7px;right:7px;bottom:7px;
  border:1px solid rgba(201,152,42,.55)}

/* Zócalos: una franja del mismo azul detrás de cada onda, para que
   el color llegue al borde exacto de la hoja aunque el renderizador
   deje un par de milímetros de holgura al escalar la página. */
.zocalo{position:absolute;left:0;width:100%;height:30px;z-index:1}
.zocalo.sup{top:0;background:#1270BC}
.zocalo.inf{bottom:0;background:#166BAF}
.onda{position:absolute;left:0;width:100%;z-index:2}
.onda.sup{top:0;height:206px} .onda.inf{bottom:0;height:206px}
.onda img{width:100%;height:100%;display:block}

.hoja{position:absolute;left:92px;right:92px;z-index:5}

table.cabecera{width:100%;border-collapse:collapse;table-layout:fixed}
table.cabecera td{vertical-align:middle;padding:0}
td.esc{width:120px;text-align:center}
td.esc img{height:122px}
td.esc.d img{height:102px}
.inst{text-align:center}
.inst .u{font-family:"Cinzel",serif;font-weight:700;font-size:18px;
  letter-spacing:2.4px;color:#0B3A6B}
.inst .f{font-weight:600;font-size:13px;letter-spacing:1.3px;color:#46566E;margin-top:5px}
.inst .c{font-weight:700;font-size:13.5px;letter-spacing:2.6px;color:#0B3A6B;margin-top:4px}

.titulo{font-family:"Cinzel",serif;font-weight:700;font-size:58px;letter-spacing:8px;
  color:#0B3A6B;text-align:center;margin-top:12px;line-height:1;text-indent:8px}

.sub{text-align:center;margin-top:7px;font-size:0}
.sub span{display:inline-block;vertical-align:middle}
.sub .l{height:1px;width:118px;background:#C9982A;margin:0 14px}
.sub .t{font-family:"Montserrat",sans-serif;font-weight:600;font-size:13.5px;
  letter-spacing:6px;color:#46566E}
.sub .rombo{width:7px;height:7px;background:#C9982A;margin:0 8px}

.otorgado{text-align:center;font-size:10.5px;letter-spacing:4px;color:#8A96A6;
  margin-top:12px;font-weight:600}
.nombre{font-family:"Great Vibes",cursive;color:#12294A;text-align:center;
  line-height:1.16;margin-top:8px}
.raya{height:1.5px;background:#C9982A;margin:8px auto 0;width:78%}

.parrafo{font-family:"Cormorant",serif;font-size:20px;line-height:1.45;
  text-align:center;color:#26334A;margin-top:12px;padding:0 46px}
.parrafo b{font-weight:600;color:#0B3A6B}

/* Las 40 horas, centradas con tabla para no depender de flex */
.horas{text-align:center;margin-top:8px;font-size:0;line-height:1}
.horas span{display:inline-block;vertical-align:middle}
.horas .n{font-family:"Cinzel",serif;font-size:26px;font-weight:700;color:#8A6400;
  letter-spacing:.5px}
.horas .t{font-family:"Montserrat",sans-serif;font-weight:600;font-size:12.5px;
  letter-spacing:3.6px;color:#46566E;margin-left:11px}
.horas .b{width:1px;height:20px;background:#C9982A;margin:0 11px}

.rot{text-align:center;font-weight:600;font-size:11px;letter-spacing:4px;
  color:#8A6400;margin-top:10px}
.rot i{display:block;width:44px;height:1px;background:#C9982A;margin:8px auto 0}

/* table-layout:fixed impide que un título largo ensanche la tabla:
   sin esto el documento crece y el renderizador achica todo,
   dejando una franja blanca al costado de la hoja. */
table.confs{width:100%;border-collapse:collapse;margin-top:8px;table-layout:fixed}
table.confs td{word-wrap:break-word;overflow-wrap:break-word}
td.dia{width:140px;vertical-align:top;padding:__AIREF__px 18px __AIREF__px 0;text-align:right;
  font-weight:700;font-size:13px;color:#1B7FC4;line-height:1.3}
td.dia span{display:block;font-weight:500;font-size:11px;color:#8A96A6}
td.lista{vertical-align:top;padding:__AIREF__px 0 __AIREF__px 18px;border-left:1px solid #E4DCC6}
.cf{margin-bottom:__AIRE__px}
.cf .t{font-family:"Cormorant",serif;font-weight:600;font-size:16.5px;
  line-height:1.34;color:#16202E}
.cf .e{font-size:11.5px;color:#5A6779;font-weight:500;line-height:1.32;margin-top:2px}

/* Pie: una tabla de tres columnas, firma · QR · firma */
table.pie{position:absolute;left:78px;right:78px;bottom:104px;width:__PIEW__px;
  border-collapse:collapse;table-layout:fixed;z-index:6}
table.pie > tbody > tr > td{vertical-align:top;text-align:center}
td.fm{width:38%;position:relative;height:170px}
td.qrcol{width:24%}
.rub{position:absolute;left:50%;margin-left:-88px;top:2px;height:70px}
.sel{position:absolute;opacity:.75}
td.izq .sel{right:-46px;top:26px;height:92px}
td.der .sel{right:-52px;top:34px;height:86px}
.linea{height:1.2px;background:#16202E;width:272px;margin:74px auto 0}
.fn{font-family:"Montserrat",sans-serif;font-size:11.5px;font-weight:700;
  margin-top:7px;color:#12294A}
.fc{font-family:"Montserrat",sans-serif;font-size:9.5px;font-weight:600;
  line-height:1.45;margin-top:4px;color:#5A6779;letter-spacing:.6px}

.qr{text-align:center;padding-top:16px}
.qr img{width:92px;height:92px;display:block;margin:0 auto;padding:5px;
  background:#fff;border:1px solid #E4DCC6}
.qr .cod{font-size:11px;font-weight:700;margin-top:5px;letter-spacing:2px;color:#0B3A6B}
.qr .ver{font-size:7.5px;color:#98A2B0;margin-top:3px;letter-spacing:.4px}
""").replace('__ALTO__', str(ALTO)).replace('__ANCHO__', str(ANCHO)).replace('__PIEW__', str(ANCHO-156)).replace('__AIRE__', str(aire)).replace('__AIREF__', str(aire+2))


def construir_html(datos, REC, con_firmas):
    filas = ''
    for dia, items in agrupar_por_dia(datos['codigos']):
        lis = ''.join(
            '<div class="cf"><div class="t">%s</div><div class="e">%s</div></div>'
            % (escapar(t), escapar(e)) for t, e, _ in items)
        d1, d2 = dia.rsplit(' ', 1)
        filas += ('<tr><td class="dia">%s %s<span>de agosto</span></td>'
                  '<td class="lista">%s</td></tr>' % (escapar(d1), d2, lis))

    def firma(clase, quien, rub, sel):
        img = ''
        if con_firmas:
            if rub: img += '<img class="rub" src="%s">' % rub
            if sel: img += '<img class="sel" src="%s">' % sel
        return ('<td class="fm %s">%s<div class="linea"></div>'
                '<div class="fn">%s</div><div class="fc">%s<br>%s</div></td>'
                % (clase, img, quien[0], quien[1], quien[2]))

    url = CFG['base_verificacion'].rstrip('/') + '/verificar.html?c=' + datos['codigo']

    # El encabezado va SIEMPRE en la misma posición: los escudos, el
    # título y el nombre no se mueven de un certificado a otro.
    # El aire sobrante se reparte DENTRO de la lista de conferencias,
    # separando más los renglones cuando hay menos.
    n = len(datos['codigos'])
    arriba = 118
    aire = {6:10, 7:7}.get(n, 4)

    return """<!DOCTYPE html><html><head><meta charset="utf-8"><style>%s</style></head><body>
<div class="zocalo sup"></div><div class="zocalo inf"></div>
<div class="marco"></div>
<div class="onda sup"><img src="%s"></div>
<div class="onda inf"><img src="%s"></div>
<div class="hoja" style="top:%dpx">
  <table class="cabecera"><tr>
    <td class="esc"><img src="%s"></td>
    <td><div class="inst">
    <div class="u">UNIVERSIDAD MAYOR DE SAN ANDRÉS</div>
    <div class="f">FACULTAD DE CIENCIAS ECONÓMICAS Y FINANCIERAS</div>
    <div class="c">CARRERA CONTADURÍA PÚBLICA</div></div></td>
    <td class="esc d"><img src="%s"></td>
  </tr></table>
  <div class="titulo">CERTIFICADO</div>
  <div class="sub"><span class="l"></span><span class="rombo"></span><span
    class="t">DE PARTICIPACIÓN</span><span class="rombo"></span><span class="l"></span></div>
  <div class="otorgado">SE OTORGA EL PRESENTE A</div>
  <div class="nombre" style="font-size:%dpx">%s</div>
  <div class="raya"></div>
  <div class="parrafo">Por su participación en las <b>%s</b>, realizadas %s en
    conmemoración del <b>%s</b>, aprobadas mediante <b>Resolución HCF N° %s</b>.</div>
  <div class="horas"><span class="n">%d</span><span class="b"></span><span
    class="t">HORAS ACADÉMICAS</span></div>
  <div class="rot">CONFERENCIAS CURSADAS<i></i></div>
  <table class="confs">%s</table>
</div>
<table class="pie"><tr>
  %s
  <td class="qrcol"><div class="qr"><img src="%s"><div class="cod">%s</div>
    <div class="ver">Escanea para verificar</div></div></td>
  %s
</tr></table></body></html>""" % (
        construir_css(REC, aire), REC['onda_sup'], REC['onda_inf'], arriba,
        REC['logo_carrera'], REC['logo_oad'],
        tam_nombre(datos['nombre']), escapar(datos['nombre']),
        CFG['evento'], CFG['fechas'], CFG['aniversario'],
        CFG['resolucion'], CFG['horas'], filas,
        firma('izq', CFG['director'], REC['firma_dir'], REC['sello_dir']),
        qr_b64(url), datos['codigo'],
        firma('der', CFG['decano'], REC['firma_dec'], REC['sello_dec']))


# ─────────────────────────────────────────────────────────────
#  LECTURA DEL CSV
# ─────────────────────────────────────────────────────────────

def leer_csv(ruta):
    with open(ruta, encoding='utf-8-sig') as f:
        filas = list(csv.DictReader(f))

    def col(fila, *nombres):
        for n in nombres:
            for k in fila:
                if k and k.strip().lower() == n.lower():
                    return str(fila[k]).strip()
        return ''

    salida = []
    for f in filas:
        cod = col(f, 'Codigo', 'Código').upper()
        if not cod: continue
        codigos = [c.strip().upper() for c in col(f, 'Codigos', 'Códigos').split(',') if c.strip()]
        salida.append({
            'codigo':  cod,
            'nombre':  col(f, 'Nombre completo', 'Nombre'),
            'ru':      col(f, 'RU'),
            'anio':    re.sub(r'\D', '', col(f, 'Año', 'Ano')) or '',
            'grupo':   col(f, 'Grupo'),
            'codigos': codigos,
        })
    salida.sort(key=lambda x: x['nombre'].lower())
    return salida


# ─────────────────────────────────────────────────────────────
#  REGISTRO PARA LA VERIFICACIÓN
# ─────────────────────────────────────────────────────────────

def escribir_registro(gente, destino):
    """certificados.js — lo que lee verificar.html en GitHub Pages."""
    conf = [[CONFS[c][0], CONFS[c][1], CONFS[c][2], CONFS[c][3]] for c in ORDEN]
    idx = {c: i for i, c in enumerate(ORDEN)}

    reg = {}
    for p in gente:
        reg[p['codigo']] = [p['nombre'], p['ru'], p['anio'], p['grupo'],
                            sorted(idx[c] for c in p['codigos'] if c in idx)]

    meta = {'evento': CFG['evento'], 'fechas': CFG['fechas_corta'],
            'resolucion': CFG['resolucion'], 'horas': CFG['horas']}

    txt = ('/* Registro de certificados · OAD 2026\n'
           '   Generado automáticamente. No editar a mano. */\n'
           'window.CERT_META = %s;\n'
           'window.CERT_CONF = %s;\n'
           'window.CERTIFICADOS = %s;\n' % (
               json.dumps(meta, ensure_ascii=False),
               json.dumps(conf, ensure_ascii=False),
               json.dumps(reg, ensure_ascii=False, separators=(',', ':'))))

    with open(destino, 'w', encoding='utf-8') as f:
        f.write(txt)
    return len(txt)


# ─────────────────────────────────────────────────────────────
#  GENERACIÓN DE LOS PDF
# ─────────────────────────────────────────────────────────────

def _una(args):
    """Renderiza un certificado. Se ejecuta en paralelo."""
    html, pdf = args
    subprocess.run([WK, '--enable-local-file-access', '--page-size', CFG['papel'],
                    '-T', '0', '-B', '0', '-L', '0', '-R', '0', '-q', html, pdf],
                   check=True,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    os.remove(html)
    return pdf


def unir(pdfs, destino):
    """
    Une las páginas en un solo archivo. Se prefiere pypdf porque es
    Python puro: no obliga a instalar poppler ni a tocar el PATH.
    """
    try:
        from pypdf import PdfWriter
    except ImportError:
        try:
            from PyPDF2 import PdfMerger as PdfWriter
        except ImportError:
            PdfWriter = None

    if PdfWriter is not None:
        w = PdfWriter()
        for p in pdfs:
            w.append(p)
        with open(destino, 'wb') as f:
            w.write(f)
        w.close()
        return

    if shutil.which('pdfunite'):
        tanda, parciales = 150, []
        tmp = os.path.dirname(pdfs[0])
        if len(pdfs) <= tanda:
            subprocess.run(['pdfunite'] + pdfs + [destino], check=True)
            return
        for i in range(0, len(pdfs), tanda):
            p = os.path.join(tmp, 'grupo_%04d.pdf' % i)
            subprocess.run(['pdfunite'] + pdfs[i:i+tanda] + [p], check=True)
            parciales.append(p)
        subprocess.run(['pdfunite'] + parciales + [destino], check=True)
        return

    raise RuntimeError('Falta pypdf. Instálalo con:  pip install pypdf')


def render(gente, REC, con_firmas, destino):
    """
    Cada página se renderiza por separado y luego se unen. Es la vía
    universal: algunas compilaciones de wkhtmltopdf no aceptan varios
    documentos de entrada a la vez.
    """
    from multiprocessing import Pool, cpu_count
    tmp = tempfile.mkdtemp(prefix='cert_')
    hilos = max(1, min(cpu_count(), 8))

    try:
        tareas = []
        for i, p in enumerate(gente):
            base = os.path.join(tmp, '%05d' % i)
            with open(base + '.html', 'w', encoding='utf-8') as f:
                f.write(construir_html(p, REC, con_firmas))
            tareas.append((base + '.html', base + '.pdf'))

        hechos = []
        with Pool(hilos) as pool:
            for n, pdf in enumerate(pool.imap(_una, tareas), 1):
                hechos.append(pdf)
                if n % 25 == 0 or n == len(tareas):
                    print('   %d / %d' % (n, len(tareas)))

        hechos.sort()
        unir(hechos, destino)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def main():
    if len(sys.argv) < 2:
        print(__doc__); sys.exit(1)

    csv_ruta = sys.argv[1]
    if not os.path.exists(csv_ruta):
        print('No encuentro el archivo:', csv_ruta); sys.exit(1)

    if not WK:
        print('\n  FALTA wkhtmltopdf.\n'
              '  Descárgalo de https://wkhtmltopdf.org/downloads.html\n'
              '  e instálalo. Después vuelve a ejecutar esto.\n')
        sys.exit(1)
    try:
        import qrcode  # noqa
    except ImportError:
        print('\n  FALTA la librería qrcode.\n'
              '  Instálala con:  pip install qrcode pillow pypdf\n')
        sys.exit(1)

    r = CFG['recursos']
    REC = {
        'onda_sup':     b64(os.path.join(r, 'onda-sup.png')) or b64(os.path.join(r, 'onda-sup.svg')),
        'onda_inf':     b64(os.path.join(r, 'onda-inf.png')) or b64(os.path.join(r, 'onda-inf.svg')),
        'logo_carrera': b64(os.path.join(r, 'logo-carrera-hd.png')),
        'logo_oad':     b64(os.path.join(r, 'logo-oad.png')),
        'firma_dir':    b64(os.path.join(r, 'firma-director.png')),
        'sello_dir':    b64(os.path.join(r, 'sello-direccion.png')),
        'firma_dec':    b64(os.path.join(r, 'firma-decano.png')),
        'sello_dec':    b64(os.path.join(r, 'sello-decanato.png')),
    }
    faltan = [k for k in ('onda_sup','onda_inf','logo_carrera','logo_oad') if not REC[k]]
    if faltan:
        print('Faltan recursos en "%s": %s' % (r, ', '.join(faltan))); sys.exit(1)

    gente = leer_csv(csv_ruta)
    if not gente:
        print('El CSV no tiene filas con código.'); sys.exit(1)

    os.makedirs(CFG['salida'], exist_ok=True)
    print('\nCertificados a generar: %d\n' % len(gente))

    # Se calibra con el certificado más cargado: si ese entra en una
    # hoja, todos los demás entran.
    print('0. Calibrando el alto de página para tu equipo')
    mas_largo = max(gente, key=lambda p: len(p['codigos']))
    calibrar_alto(mas_largo, REC)
    print()

    js = os.path.join(CFG['salida'], 'certificados.js')
    n = escribir_registro(gente, js)
    print('1. Registro de verificación  →  %s  (%d KB)' % (js, n//1024))

    print('\n2. PDF para imprenta')
    imp = os.path.join(CFG['salida'], 'certificados-IMPRENTA.pdf')
    render(gente, REC, False, imp)

    print("""
════════════════════════════════════════════
 LISTO

 %s
 %s

 SIGUIENTE PASO
 Sube certificados.js a tu repositorio de GitHub,
 junto a verificar.html. Sin ese archivo los QR
 impresos no van a validar.
════════════════════════════════════════════
""" % (imp, js))


if __name__ == '__main__':
    main()
