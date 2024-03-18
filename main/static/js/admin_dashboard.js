// Sidebar functionality
const sideMenu = document.querySelector("aside");
const menuBtn = document.querySelector("#menu-btn");
const closeBtn = document.querySelector("#close-btn");

menuBtn.addEventListener('click', () => {
    sideMenu.style.float = 'left'; // This might not be necessary
    sideMenu.style.display = 'block'; // Show sidebar
});

closeBtn.addEventListener('click', () => {
    sideMenu.style.display = 'none'; // Hide sidebar
});

// Function to get the current date and day
function getCurrentDateAndDay() {
    const daysOfWeek = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];
    const currentDate = new Date();
    const day = currentDate.getDate();
    const month = currentDate.toLocaleString('default', { month: 'long' });
    const year = currentDate.getFullYear();
    const dayOfWeek = daysOfWeek[currentDate.getDay()];

    const formattedDate = `${day}<span class="small-exponent">th</span> of ${month}, ${dayOfWeek}`;
    return formattedDate;
}

// Display the current date and day in the specified element
const dateContainer = document.getElementById('date-container');
if (dateContainer) {
    dateContainer.innerHTML = getCurrentDateAndDay();
}

// Dropdown functionality
function toggleDropdown() {
    const dropdownContent = document.getElementById('dropdown-content');
    if (dropdownContent) {
        dropdownContent.style.display = (dropdownContent.style.display === 'block') ? 'none' : 'block';
    }
}

// Flashes handling
const flashes = document.querySelectorAll('.flash');
flashes.forEach(function(flash) {
    setTimeout(function() {
        flash.style.opacity = 0;
        flash.addEventListener('transitionend', function() {
            flash.remove();
        });
    }, 3000);
});

// Tooltips (using jQuery)
$(document).ready(function() {
    $('#tooltip, #tooltip2, #tooltip3').hover(function() {
        $(this).find('#tooltipText, #tooltipText2, #tooltipText3').css({
            'top': '-1rem',
            'visibility': 'visible',
            'opacity': '1'
        });
    }, function() {
        $(this).find('#tooltipText, #tooltipText2, #tooltipText3').css({
            'top': '100%',
            'visibility': 'hidden',
            'opacity': '0'
        });
    });
});
