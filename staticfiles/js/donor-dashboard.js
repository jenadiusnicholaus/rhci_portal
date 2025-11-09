$(document).ready(function() {
  // Sidebar toggle functionality
  $('#sidebar-toggle').on('click', function() {
    $('#sidebar').toggleClass('collapsed');
    $('.main-content').toggleClass('sidebar-collapsed');
  });
  
  $('#collapse-sidebar').on('click', function() {
    $('#sidebar').toggleClass('collapsed');
    $('.main-content').toggleClass('sidebar-collapsed');
  });
  
  // Close messages
  $('.close-message').on('click', function() {
    $(this).parent().fadeOut(300, function() {
      $(this).remove();
    });
  });
  
  // Dropdown menu
  $('.user-profile').on('click', function() {
    $('.dropdown-menu').toggleClass('active');
  });
  
  // Close dropdown when clicking elsewhere
  $(document).on('click', function(e) {
    if (!$(e.target).closest('.user-profile').length) {
      $('.dropdown-menu').removeClass('active');
    }
  });
  
  // Make charts responsive
  $(window).on('resize', function() {
    if (typeof Chart !== 'undefined') {
      Chart.instances.forEach(chart => {
        chart.resize();
      });
    }
  });
  
  // Initialize any tooltips
  if (typeof bootstrap !== 'undefined' && bootstrap.Tooltip) {
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
      return new bootstrap.Tooltip(tooltipTriggerEl);
    });
  }
  
  // Initialize tabs if present
  $('.tab-btn').on('click', function() {
    var tabId = $(this).attr('data-tab');
    
    $('.tab-btn').removeClass('active');
    $(this).addClass('active');
    
    $('.tab-pane').removeClass('active');
    $('#' + tabId).addClass('active');
  });
});

// Function to load patient details dynamically
function loadPatientDetails(patientId) {
  $.ajax({
    url: `/api/patients/${patientId}/`,
    method: 'GET',
    success: function(response) {
      // Update the patient details UI
      $('#patient-name').text(response.name);
      $('#patient-age').text(response.age);
      $('#patient-condition').text(response.condition);
      $('#treatment-progress').css('width', response.treatment_progress + '%');
      $('#progress-text').text(response.treatment_progress + '% Complete');
      
      // If there's a photo available
      if (response.photo) {
        $('#patient-photo').attr('src', response.photo);
      }
      
      // Update the treatments list
      var treatmentsList = '';
      if (response.treatments && response.treatments.length > 0) {
        response.treatments.forEach(function(treatment) {
          treatmentsList += `
            <div class="treatment-item">
              <div class="treatment-date">
                <span class="date">${formatDate(treatment.date).day}</span>
                <span class="month">${formatDate(treatment.date).month}</span>
              </div>
              <div class="treatment-details">
                <h4 class="treatment-name">${treatment.name}</h4>
                <p class="treatment-hospital"><i class="fas fa-hospital"></i> ${treatment.hospital}</p>
              </div>
              <div class="treatment-cost">
                <span class="cost-label">Est. Cost:</span>
                <span class="cost-value">${treatment.estimated_cost} TZS</span>
              </div>
            </div>
          `;
        });
      } else {
        treatmentsList = '<p class="no-data">No treatments scheduled for this patient.</p>';
      }
      
      $('#treatments-list').html(treatmentsList);
    },
    error: function(error) {
      console.error('Error loading patient details:', error);
      showNotification('Error loading patient details. Please try again.', 'error');
    }
  });
}

// Helper function to format date
function formatDate(dateString) {
  const date = new Date(dateString);
  return {
    day: date.getDate(),
    month: date.toLocaleString('default', { month: 'short' })
  };
}

// Function to show notifications
function showNotification(message, type = 'info') {
  const notification = `
    <div class="message ${type}">
      ${message}
      <button class="close-message"><i class="fas fa-times"></i></button>
    </div>
  `;
  
  $('.messages').append(notification);
  
  // Auto-close after 5 seconds
  setTimeout(function() {
    $('.message').first().fadeOut(300, function() {
      $(this).remove();
    });
  }, 5000);
  
  // Make notification dismissable
  $('.close-message').on('click', function() {
    $(this).parent().fadeOut(300, function() {
      $(this).remove();
    });
  });
}