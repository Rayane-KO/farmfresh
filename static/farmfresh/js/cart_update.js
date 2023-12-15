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
    var quantityElement = button.closest(".qty");
    console.log("product:", productElement);
    console.log("qty:", quantityElement)
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
        var productId = $(this).data("product-id");
        var url = $(this).data("add-url");
        var token = getToken();
        console.log(productId)
        $.ajax({
            type: "post",
            url: url,
            data: { pk: productId, csrfmiddlewaretoken: token },
            dataType: "json",
            success: function(data){
                    console.log(data.status);
            },
            error: function(error){
                console.log(error);
            },
        });
    });

    $(".remove_from_cart").on("click", function(){
        var button = $(this);
        var productId = $(this).data("product-id");
        var url = $(this).data("add-url");
        var unit = $(this).data("unit");
        var price = $(this).data("price");
        var token = getToken();
        $.ajax({
            type: "post",
            url: url,
            data: { pk: productId, csrfmiddlewaretoken: token },
            dataType: "json",
            success: function(data){
                    var quantityElement = $("#qty-" + productId);
                    var productTotalElement = $("#total-" + productId);
                    var totalElement = $("#total");
                    var card = $("#card-" + productId);
                    var currentQty = parseInt(quantityElement.text().split(": ")[1]);
                    var currentTotal = parseFloat(productTotalElement.text().split(": ")[1]).toFixed(2);
                    var total = parseFloat(totalElement.text().split(": ")[1]).toFixed(2);
                    var unitString= "";
                    console.log(data)
                    if (currentQty === 1){
                        card.remove()
                    }
                    else{
                        if (unit === "piece"){
                        unitString = " Pieces";
                        }
                        else unitString = " Kg";
                        quantityElement.text("Quantity: " + (currentQty-1) + unitString);
                    }
                    productTotalElement.text("Total: " + (currentTotal-price).toFixed(2));
                    totalElement.text("Total: " + (total-price).toFixed(2));
            },
            error: function(error){
                console.log(error);
            },
        });
    });
})