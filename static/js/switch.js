var index = 0
const total = 2
var optionNames = ["Prediction", "Interpolation"]

function switchLeft() {
    console.log("switch left");
    index += -1;
    update();
}
function switchRight() {
    console.log("switch right");
    index += 1;
    update(index);
}

function update() {
    console.log("updating with index="+index);
    if (index >= total) {
        index = index-total;
    } else if (index < 0) {
        index = index + total;
    }
    console.log("fixed index="+index);
    console.log("");
    $("#option-name").text(optionNames[index]);


    var allOptions = document.getElementById("main-container").querySelectorAll(".visible-template"); 
    for(var j = 0; j < allOptions.length; ++j){
        allOptions[j].classList.remove("visible-template");
    } 
    for (i = 0; i < total; i++) {
        id = "option"+i;
        if (i == index) {
            $("#"+id).addClass("visible-template");
        }
    }
    // console.log(document.getElementById("option0").classList)
    // console.log(document.getElementById("option1").classList)

    toTop();
}



function toTop() {
    window.scrollTo(0,0);
}