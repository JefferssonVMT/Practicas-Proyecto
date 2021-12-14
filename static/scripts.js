
function vendido(id){
    $.getJSON("/vendido?id="+id, function(data){

        $("#pub"+id).remove();
        $(".error").remove();

        if (!$(".tabla_filas").length){
            $("#cabecera_tabla").remove();
        }

        console.log(data);
    });
};

function cargar_mas() {

    $.getJSON("/cargar_mas", function(data) {

        mostrarInfo(data);
    });
};

$("#btn_buscar").ready(function(){
    $('#btn_buscar').click(function(){
        
        let q = $("#input_buscar").val();
        console.log(q);

        if (q){
            $.getJSON("/search?q="+q, function(data){
                $("#pubs").empty();
                $("#load").remove();
                mostrarInfo(data);
                $("#input_buscar").val("");
                q = null;
            });
        };
        
    });
});


function mostrarInfo(data){
    for (let i = 0; i < data.length; i++) {
        /*
        $("#main").append('\
         <div class="publicacion container p-0">\
             <div class="container pl-3 pr-3 pb-0">\
                 <h4>' + data[i]['user'] + '</h4>\
                 <h5>' + data[i]['titulo'] + '</h5>\
                 <p>' + data[i]['descripcion'] + '</p>\
             </div>\
             <img src=\"'+ data[i]['imagen1'] +'" class="p_imagen" alt="imagen">\
             <div class="container text-center">\
                 <a type="button" onclick="redirect('+data[i]['pid']+')" class="btn btn-light m-2"><i class="fas fa-info-circle" style="color: gray;"></i>  Ver mas... </a> \
             </div>\
         </div>');
         */

        var div1 = document.createElement("div");
        div1.className = "publicacion container p-0";
         
        var div2 = document.createElement("div");
        div2.className = "container pl-3 pr-3 pb-0";
        div1.appendChild(div2);

        var user = document.createElement("h4");
        user.innerHTML = data[i].user;
        div2.appendChild(user);

        var titulo = document.createElement("h5");
        titulo.innerHTML = data[i].titulo;
        div2.appendChild(titulo);

        var desc = document.createElement("p");
        desc.innerHTML = data[i].descripcion;
        div2.appendChild(desc);

        var img = document.createElement("img");            
        img.src = data[i].imagen1;
        img.className = "p_imagen";
        img.alt = "imagen";
        div1.appendChild(img);

        var otroDiv = document.createElement("div");
        otroDiv.className = "container text-center";
        div1.appendChild(otroDiv);

        var link = document.createElement("a");
        link.type = "button";
        link.addEventListener('click', function(){
            redirect(data[i].pid);
        });
        link.className = "btn btn-light m-2";
        var icono = document.createElement("i");
        icono.className = "fas fa-info-circle";
        icono.style = "color: gray;"
        link.appendChild(icono);
        link.appendChild(document.createTextNode(" Ver mas..."));
        otroDiv.appendChild(link);
     
        document.getElementById("pubs").appendChild(div1);
    };
};

$(document).ready(function(){
    for(let i = 1; i <= 10; i++){
        $("#cat_"+i).click(function(){
            
            $.getJSON("/search?id_categoria="+i, function(data){
                $("#pubs").empty();
                $("#load").remove();
                mostrarInfo(data);
                $("#input_buscar").val("");
            });
        });

        $("#cat_"+i).mouseover(function(){
            $("#cat_"+i).css("color","rgb(38, 228, 38)");
        });

        $("#cat_"+i).mouseout(function(){
            $("#cat_"+i).css("color","white");
        });
    };
});

function redirect(id){
    window.location.href = "detalles?id=" + id;
};