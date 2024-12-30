const todas = document.getElementById('todas')
const castillaLeon = document.getElementById('castilla_leon')
const comunidadValenciana = document.getElementById('comunidad_valenciana')
const euskadi = document.getElementById('euskadi')
const btnEnviar = document.getElementById('enviar')
const btnReiniciarBd = document.getElementById('reiniciar_db')
const textArea = document.getElementById('result_box')


function activarTodas(){
    if(castillaLeon.checked && comunidadValenciana.checked && euskadi.checked){
        todas.checked = true
    }
    else{
        todas.checked = false;
    }
}

castillaLeon.addEventListener('change', activarTodas);
comunidadValenciana.addEventListener('change', activarTodas);
euskadi.addEventListener('change', activarTodas);
todas.addEventListener('change', function(){
    if(todas.checked){
        castillaLeon.checked = true
        comunidadValenciana.checked = true
        euskadi.checked = true
    }
    else{
        castillaLeon.checked = false
        comunidadValenciana.checked = false
        euskadi.checked = false
    }
})


btnEnviar.addEventListener('click', function(){
    fetch('/main/cargar-almacen-datos/' ,{
        method: 'POST',
        headers:{
            'Content-Type': 'application/json',
        },
        body : JSON.stringify({
            'castilla-Leon': castillaLeon.checked,
            'comunidad-Valenciana': comunidadValenciana.checked,
            'euskadi': euskadi.checked,
        }),
    })
    .then(response => response.json())
    .then(data =>{
        textArea.textContent = JSON.stringify(data.informe, null, 2);
    })
    .catch(error => {
        console.error('Error:', error);
        textArea.textContent = 'Ocurrió un error al cargar los datos.';
    });
})

btnReiniciarBd.addEventListener('click', function(){
    fetch('/main/vaciar-almacen-datos/', {	
        method: 'POST',
        headers:{
            'Content-Type': 'application/json',
        },
    })
    .then(response => response.json())
    .then(data =>{
        if(data.status == 'success'){
            textArea.textContent = 'Base de datos reiniciada correctamente'
        }else{
            alert("Algo ha slido mal:" + data.message)
        }
    })
})