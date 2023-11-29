function getToken(){
    var val = "; " + document.cookie;
    var parts = val.split("; csrftoken=");
    if (parts.length === 2){
        return parts.pop().split(";").shift()
    }
}

function updateCartItem(button, unit){
    console.log("updating for:", button);
    var productElement = button.closest(".cart-item");
    var quantityElement = productElement.find(".qty");
    var currentQty = parseInt(quantityElement.text().split(": ")[1]);
    var unitString= "";

    if (currentQty === 1){
        productElement.remove()
        
    } else{
        if (unit === "piece"){
            unitString = " Pieces";
        }
        else unitString = " Kg";
        quantityElement.text("Quantity: " + (currentQty-1) + unitString);
    }
}

$(document).ready(function(){
    $(".add_to_cart").on("click", function(){
        var button = $(this);
        var productId = $(this).data("product-id");
        var url = $(this).data("add-url");
        var unit = $(this).data("unit");
        var debug = button.data("debug");
        var token = getToken();
        $.ajax({
            type: "post",
            url: url,
            data: { pk: productId, csrfmiddlewaretoken: token },
            dataType: "json",
            success: function(data){
                    var productElement = button.closest(".cart-item");
                    var quantityElement = productElement.find(".qty");
                    var currentQty = parseInt(quantityElement.text().split(": ")[1]);
                    var unitString= "";
                    if (currentQty === 1){
                        productElement.remove()
                    }
                    else{
                        if (unit === "piece"){
                        unitString = " Pieces";
                        }
                        else unitString = " Kg";
                        quantityElement.text("Quantity: " + (currentQty-1) + unitString);
                    }
            },
            error: function(error){
                console.log(error);
            },
        });
    });
})