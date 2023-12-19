// https://codepen.io/83338/pen/KdVPLd
function updateFavFarmer(){
    var userId = document.querySelector(".user-info").getAttribute("data-user-id")
    var favoritesId = "favorites_" + userId
    console.log(favoritesId)
    var favorites = JSON.parse(localStorage.getItem(favoritesId)) || [];
    document.querySelectorAll(".fav-button").forEach(function(button){
        var farmerId = button.getAttribute("data-farmer-id");
        var isAuthenticated = button.getAttribute("data-auth");
        if (farmerId !== userId && isAuthenticated){
            var star = button.querySelector(".fa-star");
            if (favorites.includes(farmerId)){
                star.classList.add("fa-solid")
            }
            button.addEventListener("click", function(){
                var idx = favorites.indexOf(farmerId);
                if (idx === -1){
                    favorites.push(farmerId);
                    star.classList.add("fa-solid");
                }
                else{
                    favorites.splice(idx, 1);
                    star.classList.remove("fa-solid");
                }
                localStorage.setItem(favoritesId, JSON.stringify(favorites));
            });
        }
    });
};

document.addEventListener("DOMContentLoaded", updateFavFarmer);