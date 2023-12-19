function toggleIfFarmer(){
    const userType = document.querySelector("#id_user_type");
    const farmNr = document.querySelector("#farm_nr");

    function toggleFarmNumber(){
        if (userType.value === "farmer"){
            farmNr.style.display = "block";
        }
        else farmNr.style.display = "none";
    }

    userType.addEventListener("change", toggleFarmNumber);
    toggleFarmNumber()
}

function checkUsername(username) {
    var feedbackElement = $("#feedback-icon");
    var iconElement = feedbackElement.find("i");
    var url = feedbackElement.data("url");
    $.ajax({
        type: "GET",
        url: url, 
        data: { "username": username },
        success: function(data) {
            console.log(data.available)
            if (data.available){
                iconElement.addClass("fa-check").removeClass("fa-xmark");
                iconElement.css("color", "#027e1b");
                iconElement.attr("title", "Username is available!");
            } else {
                iconElement.addClass("fa-xmark").removeClass("fa-check");
                iconElement.css("color", "#dc0909");
                iconElement.attr("title", "Username is not available!");
            }
        },
        error: function (error){
            console.error("Error");
        }
    });
}

document.addEventListener("DOMContentLoaded", function(){
    $("#id_username").on("input", function(){
        var username = $(this).val();
        checkUsername(username);
    })
    toggleIfFarmer();

})