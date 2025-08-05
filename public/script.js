// Buffer Platform Script
const API_URL = 'http://localhost:3000';

// Schedule type mapping to cron expressions
const scheduleTypes = {
    '1min': '* * * * *',
    '5min': '*/5 * * * *',
    '15min': '*/15 * * * *',
    '30min': '*/30 * * * *',
    '45min': '*/45 * * * *',
    '60min': '0 * * * *',
    '24h': '0 0 * * *',
    'custom': ''
};

// Function to update cron expression based on selection
function updateCronExpression() {
    const scheduleType = document.getElementById('scheduleType');
    const cronExpressionInput = document.getElementById('cronExpression');
    
    if (!scheduleType || !cronExpressionInput) {
        console.error('Form elements not found');
        return;
    }

    if (scheduleType.value === 'custom') {
        cronExpressionInput.value = '';
        cronExpressionInput.disabled = false;
        cronExpressionInput.placeholder = 'Enter cron expression...';
        cronExpressionInput.focus();
    } else {
        cronExpressionInput.value = scheduleTypes[scheduleType.value];
        cronExpressionInput.disabled = true;
    }
}

// Function to add new schedule
async function addSchedule(event) {
    event.preventDefault();

    const schedule = {
        name: document.getElementById('name').value,
        url: document.getElementById('url').value,
        method: document.getElementById('method').value,
        cronExpression: document.getElementById('cronExpression').value
    };

    try {
        const response = await fetch(`${API_URL}/schedule`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(schedule)
        });

        if (!response.ok) {
            throw new Error('Error creating schedule');
        }

        alert('Schedule created successfully!');
        document.getElementById('scheduleForm').reset();
        loadSchedules();
    } catch (error) {
        alert(`Error: ${error.message}`);
    }
}

// Function to delete schedule
async function deleteSchedule(id) {
    if (confirm('Are you sure you want to delete this schedule?')) {
        try {
            const response = await fetch(`${API_URL}/schedule/${id}`, {
                method: 'DELETE'
            });

            if (!response.ok) {
                throw new Error('Error deleting schedule');
            }

            loadSchedules();
        } catch (error) {
            alert(`Error: ${error.message}`);
        }
    }
}

// Function to load existing schedules
async function loadSchedules() {
    try {
        const response = await fetch(`${API_URL}/schedules`);
        const schedules = await response.json();

        const schedulesList = document.getElementById('schedulesList');
        schedulesList.innerHTML = '';

        schedules.forEach(schedule => {
            const li = document.createElement('li');
            li.className = 'schedule-item';
            
            const scheduleInfo = document.createElement('span');
            scheduleInfo.textContent = `${schedule.name} - ${schedule.url} (${schedule.cronExpression})`;
            
            const deleteButton = document.createElement('button');
            deleteButton.textContent = 'Delete';
            deleteButton.className = 'delete-button';
            deleteButton.onclick = () => deleteSchedule(schedule.id);
            
            li.appendChild(scheduleInfo);
            li.appendChild(deleteButton);
            schedulesList.appendChild(li);
        });
    } catch (error) {
        console.error('Error loading schedules:', error);
    }
}

// Event listeners
document.getElementById('scheduleForm').addEventListener('submit', addSchedule);
document.getElementById('scheduleType').addEventListener('change', updateCronExpression);
document.addEventListener('DOMContentLoaded', () => {
    loadSchedules();
    updateCronExpression(); // Initialize cronExpression field
}); 