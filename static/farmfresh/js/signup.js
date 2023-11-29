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

document.addEventListener("DOMContentLoaded", toggleIfFarmer)