function getToken(){
    var val = "; " + document.cookie;
    var parts = val.split("; csrftoken=");
    if (parts.length === 2){
        return parts.pop().split(";").shift()
    }
}

function changeCartBadge(count){
    const badge = $("#cart-badge");
    badge.text(count)
    if (count = 0){
        badge.hide();
    } 
    else {
        badge.show();
    }
}

function updateCartBadge(){
    var token = getToken();
    var url = $("#cart-badge").data("url")
    $.ajax({
        type: "get",
        url: url,
        data: { csrfmiddlewaretoken: token },
        dataType: "json",
        success: function(data){
            changeCartBadge(data.cart_count);
        },
        error: function(error){
            console.log(error);
        },
    });
}

function updateCartList(subtotal, total, productId){
    var subtotalId = "#total-" + productId;
    var subtotalElement = $(subtotalId);
    var totalElement = $("#total");
    const totalBase = "Total: €";
    console.log(totalBase + subtotal);
    subtotalElement.text(totalBase + subtotal);
    totalElement.text(totalBase + total);
}

$(document).ready(function(){
    var redirection = false;
    updateCartBadge();

    $(".add_to_cart").on("click", function(){
        $("#basket").addClass("fa-bounce");
        setTimeout(function(){
            $("#basket").removeClass("fa-bounce");
        }, 500);
        var productId = $(this).data("product-id");
        var url = $(this).data("add-url");
        var token = getToken();
        $.ajax({
            type: "post",
            url: url,
            data: { pk: productId, csrfmiddlewaretoken: token },
            dataType: "json",
            success: function(data){
                if (data.redirect){
                    window.location.href = data.redirect;
                    redirection = true;
                } else {
                    changeCartBadge(data.cart_count);
                    updateCartList(data.subtotal, data.total, productId);
                }
            },
            error: function(xhr, status, error){
                console.error("AJAX request failed:", status, error);
                console.log("Response:", xhr.responseText);
            },
        });
    });

    $(".remove_from_cart").on("click", function(){
        $("#basket").addClass("fa-shake");
        setTimeout(function(){
            $("#basket").removeClass("fa-shake");
        }, 500);
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
                if (data.redirect){
                    window.location.href = data.redirect;
                    redirection = true;
                } else {
                    changeCartBadge(data.cart_count);
                    updateCartList(data.subtotal, data.total, productId);
                    var quantityElement = $("#qty-" + productId);
                    var card = $("#card-" + productId);
                    var currentQty = parseInt(quantityElement.text().split(": ")[1]);
                    var unitString= "";
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
                }
            },
            error: function(error){
                console.log(error);
            },
        });
    });

    $('.update').on('click', function () {
        if (!redirection){
            $(this).hide();
            $(this).siblings('.quantity-input').show();
            var quantityInput = $('.increment').siblings('.quantity');
            quantityInput.val(1);
        }
    });

    $('.decrement').on('click', function () {
        if (!redirection){
            var quantityInput = $(this).siblings('.quantity');
            var quantity = parseInt(quantityInput.val(), 10);
            if (quantity > 1) {
                quantityInput.val(quantity - 1);
            } else {
                // Optionally, you can toggle back to "Add to Cart"
                $(this).parent().siblings('.update').show();
                $(this).parent().hide();
            }
        }
    });

    $('.increment').on('click', function () {
        if (!redirection){
            var quantityInput = $(this).siblings('.quantity');
            quantityInput.val(parseInt(quantityInput.val(), 10) + 1);
        }
    });
})