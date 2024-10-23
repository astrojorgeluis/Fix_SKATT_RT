# Ska Table Top Radio Telescope - Fix

Este repositorio contiene una pequeña corrección para el código de **Ska Table Top Radio Telescope**. Todos los créditos pertenecen al equipo original: [Ska Table Top Radio Telescope GitLab Repository](https://gitlab.com/ska-telescope/ska-tabletop-radiotelescope/).

### Descripción del Fix

El fix consiste en correcciones a dos archivos clave para mejorar la compatibilidad y la interfaz:

1. **sdr_wrapper.py**  
   - Problema: Con versiones superiores de numpy (2.0 o más), el programa no funcionará.  
   - Fix: Se reemplaza la línea 41 con `np.complex128`, que es compatible con versiones superiores de numpy.

2. **tabletop_app.py**  
   - Correcciones a la interfaz gráfica del programa:  
     - Deshabilita la imagen del logo en la línea 40.  
     - Ajusta el tamaño del texto en la línea 199 para mejorar la visualización.  
     - Habilita la opción de cambiar el tamaño de la ventana en la línea 278.
