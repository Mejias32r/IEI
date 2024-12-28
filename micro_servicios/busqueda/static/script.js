async function initFilteredSearch(){
    let localidad = document.getElementById("localidad").value
    let cp = document.getElementById("codigo-postal").value
    let provincia = document.getElementById("provincia").value
    let tipo = document.getElementById("tipo").value
    console.log(localidad + cp + provincia + tipo)
}

function cancel(){
    document.getElementById("localidad").value = ""
    document.getElementById("codigo-postal").value = ""
    document.getElementById("provincia").value = ""
    document.getElementById("tipo").value = ""
}

