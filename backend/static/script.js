const droparea = document.getElementById("drop-area");
const inputfile = document.getElementById("input-file");
const previewImg = document.getElementById("preview-img");
const loadingIndicator = document.getElementById("loading-indicator");

// Editable fields
const idTypeInput = document.getElementById("id-type");
const firstNameInput = document.getElementById("first-name");
const middleNameInput = document.getElementById("middle-name");
const lastNameInput = document.getElementById("last-name");
const dobInput = document.getElementById("dob");
const addressInput = document.getElementById("address");

// Current image path
let currentImgPath = "";

//machine learning
let tmModel, maxPredictions;

// Load TM model
async function loadTMModel() {
    const URL = "/static/my_model/";
    tmModel = await tmImage.load(URL + "model.json", URL + "metadata.json");
    maxPredictions = tmModel.getTotalClasses();
    console.log("TM model loaded");
}
loadTMModel();

// Upload & process image
async function uploadImage(file) {
    if (!file) return;

    const imgLink = URL.createObjectURL(file);
    previewImg.src = imgLink;
    loadingIndicator.style.display = "block";

    const imgForTM = new Image();
    imgForTM.src = imgLink;
    imgForTM.onload = async () => {

        const prediction = await tmModel.predict(imgForTM);
        const labels = prediction.map(p => p.className);
        const probs = prediction.map(p => p.probability);
        const maxIndex = probs.indexOf(Math.max(...probs));
        const idType = labels[maxIndex];
        idTypeInput.value = idType;

        const formData = new FormData();
        formData.append("file", file);

        fetch("/upload", { method: "POST", body: formData })
        .then(res => res.json())
        .then(data => {

            firstNameInput.value = data.First_name || "";
            middleNameInput.value = data.Middle_name || "";
            lastNameInput.value = data.Last_name || "";
            dobInput.value = data.Date_of_birth || "";
            addressInput.value = data.Address || "";
            currentImgPath = data.Img_path || "";
        })
        .catch(err => {
            console.error(err);
            alert("Error processing image");
        })
        .finally(() => {
            loadingIndicator.style.display = "none";
        });
    };
}

// File select & drag & drop
inputfile.addEventListener("change", () => uploadImage(inputfile.files[0]));

droparea.addEventListener("dragover", (e) => {
    e.preventDefault();
    droparea.classList.add("dragover");
});
droparea.addEventListener("dragleave", () => droparea.classList.remove("dragover"));
droparea.addEventListener("drop", (e) => {
    e.preventDefault();
    droparea.classList.remove("dragover");
    const file = e.dataTransfer.files[0];
    uploadImage(file);
});

// Save button
document.getElementById("save-btn").addEventListener("click", () => {
    const payload = {
        ID_type: idTypeInput.value,
        First_name: firstNameInput.value,
        Middle_name: middleNameInput.value,
        Last_name: lastNameInput.value,
        Date_of_birth: dobInput.value,
        Address: addressInput.value,
        Img_path: currentImgPath
    };

    fetch("/save_guest", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
    })
    .then(res => res.json())
    .then(res => {
        if (res.status === "success") {
            alert("Guest saved! ID: " + res.guest_id);
        } else {
            alert("Failed to save guest");
        }
    });
});
