document.addEventListener('DOMContentLoaded', () => {
    const form = document.getElementById('report-form');
    const issueType = document.getElementById('issue_type');
    const additionalDetails = document.getElementById('additional_details');
  
    form.addEventListener('submit', (e) => {
      if (issueType.value === "Other" && additionalDetails.value.trim() === "") {
        e.preventDefault();
        alert("⚠️ Please provide additional details if selecting 'Other'.");
      }
    });
  });

 