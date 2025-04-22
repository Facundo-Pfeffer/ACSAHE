document.addEventListener("keydown", function(event) {
    if (event.ctrlKey && event.key === "p") {
        event.preventDefault(); // Prevent the default print dialog
        // Optional: Insert any dynamic adjustments for print layout here
        window.print(); // Open the print dialog after adjustments
    }
});