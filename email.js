document.addEventListener("DOMContentLoaded", function () {
    document.getElementById("sendEmailBtn").addEventListener("click", function () {
        const { jsPDF } = window.jspdf;
        let doc = new jsPDF();
        let graphs = document.querySelectorAll(".graph-container img");
        let yOffset = 10;
        let totalGraphs = graphs.length;
        let processedGraphs = 0;

        if (totalGraphs === 0) {
            alert("❌ No graphs found to send.");
            return;
        }

        graphs.forEach(graph => {
            let img = new Image();
            img.src = graph.src;

            img.onload = function () {
                let width = 180;
                let height = (img.height / img.width) * width;

                if (yOffset + height > 280) {
                    doc.addPage();
                    yOffset = 10;
                }

                doc.addImage(img, "PNG", 15, yOffset, width, height);
                yOffset += height + 10;
                processedGraphs++;

                if (processedGraphs === totalGraphs) {
                    // Convert PDF to Base64
                    let pdfBase64 = doc.output("datauristring").split(",")[1];

                    let emailInput = document.getElementById("emailInput").value;
                    let csrfToken = document.querySelector("[name=csrfmiddlewaretoken]").value;

                    if (!emailInput) {
                        alert("❌ Please enter an email address.");
                        return;
                    }

                    // ✅ Debugging Log
                    console.log("📌 Sending PDF Data to Backend:", { email: emailInput, pdfBase64 });

                    fetch("/send-pdf-email/", {  // Use absolute URL
                        method: "POST",
                        headers: {
                            "Content-Type": "application/json",
                            "X-CSRFToken": csrfToken
                        },
                        body: JSON.stringify({
                            email: emailInput,
                            pdfData: pdfBase64
                        })
                    })
                    .then(response => response.json())
                    .then(data => {
                        console.log("✅ Response:", data);
                        alert(data.success || data.error);
                    })
                    .catch(error => {
                        console.error("❌ Error Sending Email:", error);
                        alert("Failed to send email.");
                    });
                }
            };

            img.onerror = function () {
                console.error("❌ Error loading image:", img.src);
            };
        });
    });
});
