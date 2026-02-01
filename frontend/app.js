// API Configuration
const API_BASE_URL = 'http://localhost:8000';

// State
let currentAssignments = [];
let currentSubmissions = [];

// Tab Management
document.getElementById('tab-assignments').addEventListener('click', () => {
    switchTab('assignments');
});

document.getElementById('tab-submissions').addEventListener('click', () => {
    switchTab('submissions');
});

function switchTab(tab) {
    // Update tab buttons
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.classList.remove('active', 'border-blue-500', 'text-blue-600');
        btn.classList.add('border-transparent', 'text-gray-500');
    });
    
    const activeBtn = document.getElementById(`tab-${tab}`);
    activeBtn.classList.add('active', 'border-blue-500', 'text-blue-600');
    activeBtn.classList.remove('border-transparent', 'text-gray-500');
    
    // Update content
    document.querySelectorAll('.tab-content').forEach(content => {
        content.classList.add('hidden');
    });
    document.getElementById(`content-${tab}`).classList.remove('hidden');
    
    // Load data
    if (tab === 'assignments') {
        loadAssignments();
    } else if (tab === 'submissions') {
        loadAssignmentsForDropdown();
    }
}

// Create Assignment
document.getElementById('create-assignment-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const title = document.getElementById('assignment-title').value;
    const rubricText = document.getElementById('assignment-rubric').value;
    
    try {
        const rubric = JSON.parse(rubricText);
        
        const response = await fetch(`${API_BASE_URL}/assignments/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ title, rubric })
        });
        
        if (!response.ok) {
            throw new Error('Failed to create assignment');
        }
        
        alert('Assignment created successfully!');
        document.getElementById('create-assignment-form').reset();
        loadAssignments();
        
    } catch (error) {
        alert('Error: ' + error.message);
    }
});

// Load Assignments
async function loadAssignments() {
    try {
        const response = await fetch(`${API_BASE_URL}/assignments/`);
        const assignments = await response.json();
        currentAssignments = assignments;
        
        const container = document.getElementById('assignments-list');
        
        if (assignments.length === 0) {
            container.innerHTML = '<p class="text-gray-500">No assignments yet.</p>';
            return;
        }
        
        container.innerHTML = assignments.map(assignment => `
            <div class="border border-gray-200 rounded-lg p-4 hover:shadow-md transition">
                <div class="flex justify-between items-start">
                    <div class="flex-1">
                        <h3 class="text-lg font-semibold text-gray-900">${escapeHtml(assignment.title)}</h3>
                        <p class="text-sm text-gray-500">Created: ${new Date(assignment.created_at).toLocaleString()}</p>
                        <details class="mt-2">
                            <summary class="text-sm text-blue-600 cursor-pointer hover:text-blue-800">View Rubric</summary>
                            <pre class="mt-2 p-3 bg-gray-50 rounded text-xs overflow-x-auto">${JSON.stringify(assignment.rubric, null, 2)}</pre>
                        </details>
                    </div>
                    <button onclick="openReferenceModal(${assignment.id})" 
                            class="ml-4 bg-purple-600 text-white px-3 py-1 rounded text-sm hover:bg-purple-700">
                        Add Reference
                    </button>
                </div>
            </div>
        `).join('');
        
    } catch (error) {
        console.error('Error loading assignments:', error);
    }
}

// Load Assignments for Dropdown
async function loadAssignmentsForDropdown() {
    try {
        const response = await fetch(`${API_BASE_URL}/assignments/`);
        const assignments = await response.json();
        currentAssignments = assignments;
        
        const submissionSelect = document.getElementById('submission-assignment');
        const filterSelect = document.getElementById('filter-assignment');
        
        const options = assignments.map(a => 
            `<option value="${a.id}">${escapeHtml(a.title)}</option>`
        ).join('');
        
        submissionSelect.innerHTML = '<option value="">-- Select Assignment --</option>' + options;
        filterSelect.innerHTML = '<option value="">-- All Assignments --</option>' + options;
        
    } catch (error) {
        console.error('Error loading assignments:', error);
    }
}

// Submit Assignment
document.getElementById('submit-assignment-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const assignmentId = document.getElementById('submission-assignment').value;
    const fileInput = document.getElementById('submission-file');
    const file = fileInput.files[0];
    
    if (!file) {
        alert('Please select a file');
        return;
    }
    
    const formData = new FormData();
    formData.append('file', file);
    
    try {
        const response = await fetch(`${API_BASE_URL}/submissions/?assignment_id=${assignmentId}`, {
            method: 'POST',
            body: formData
        });
        
        if (!response.ok) {
            throw new Error('Failed to submit assignment');
        }
        
        alert('Submission uploaded! Grading in progress...');
        document.getElementById('submit-assignment-form').reset();
        
        // Auto-refresh submissions after a delay
        setTimeout(() => loadSubmissions(), 2000);
        
    } catch (error) {
        alert('Error: ' + error.message);
    }
});

// Load Submissions
document.getElementById('filter-assignment').addEventListener('change', loadSubmissions);
document.getElementById('refresh-submissions').addEventListener('click', loadSubmissions);

async function loadSubmissions() {
    const filterAssignmentId = document.getElementById('filter-assignment').value;
    const container = document.getElementById('submissions-list');
    
    try {
        let submissions = [];
        
        if (filterAssignmentId) {
            const response = await fetch(`${API_BASE_URL}/submissions/assignment/${filterAssignmentId}`);
            submissions = await response.json();
        } else {
            // Load all submissions for all assignments
            for (const assignment of currentAssignments) {
                const response = await fetch(`${API_BASE_URL}/submissions/assignment/${assignment.id}`);
                const assignmentSubmissions = await response.json();
                submissions.push(...assignmentSubmissions);
            }
        }
        
        currentSubmissions = submissions;
        
        if (submissions.length === 0) {
            container.innerHTML = '<p class="text-gray-500">No submissions yet.</p>';
            return;
        }
        
        container.innerHTML = submissions.map(submission => `
            <div class="border border-gray-200 rounded-lg p-4 hover:shadow-md transition">
                <div class="flex justify-between items-center">
                    <div class="flex-1">
                        <h3 class="text-lg font-semibold text-gray-900">${escapeHtml(submission.filename)}</h3>
                        <p class="text-sm text-gray-500">Assignment ID: ${submission.assignment_id}</p>
                        <p class="text-sm text-gray-500">Submitted: ${new Date(submission.created_at).toLocaleString()}</p>
                    </div>
                    <div class="flex items-center space-x-3">
                        ${getStatusBadge(submission.status, submission.score)}
                        ${submission.status === 'done' ? 
                            `<button onclick="showGradeDetails(${submission.id})" 
                                    class="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700">
                                Explain
                            </button>` : 
                            ''}
                    </div>
                </div>
            </div>
        `).join('');
        
    } catch (error) {
        console.error('Error loading submissions:', error);
    }
}

// Status Badge
function getStatusBadge(status, score) {
    const badges = {
        'queued': '<span class="px-3 py-1 bg-gray-200 text-gray-800 rounded-full text-sm font-medium">Queued</span>',
        'grading': '<span class="px-3 py-1 bg-yellow-200 text-yellow-800 rounded-full text-sm font-medium">Grading...</span>',
        'error': '<span class="px-3 py-1 bg-red-200 text-red-800 rounded-full text-sm font-medium">Error</span>',
        'done': `<span class="px-3 py-1 bg-green-200 text-green-800 rounded-full text-sm font-medium">Score: ${score}</span>`
    };
    return badges[status] || badges['queued'];
}

// Show Grade Details
async function showGradeDetails(submissionId) {
    try {
        const response = await fetch(`${API_BASE_URL}/submissions/${submissionId}/grade`);
        
        if (!response.ok) {
            throw new Error('Grade not found');
        }
        
        const grade = await response.json();
        
        const content = document.getElementById('grade-content');
        content.innerHTML = `
            <div class="space-y-6">
                <div class="bg-blue-50 border-l-4 border-blue-500 p-4">
                    <p class="text-sm text-blue-700 font-medium">Final Score</p>
                    <p class="text-3xl font-bold text-blue-900">${grade.score}</p>
                </div>
                
                <div>
                    <h4 class="text-lg font-semibold mb-3">Breakdown</h4>
                    <div class="bg-gray-50 rounded-lg p-4">
                        <pre class="text-sm overflow-x-auto">${JSON.stringify(grade.breakdown, null, 2)}</pre>
                    </div>
                </div>
                
                <div>
                    <h4 class="text-lg font-semibold mb-3">Feedback</h4>
                    <div class="bg-gray-50 rounded-lg p-4">
                        <p class="text-gray-700 whitespace-pre-wrap">${escapeHtml(grade.feedback)}</p>
                    </div>
                </div>
                
                <div>
                    <h4 class="text-lg font-semibold mb-3">Citations</h4>
                    <div class="space-y-2">
                        ${grade.citations.map((citation, idx) => `
                            <div class="bg-purple-50 border-l-4 border-purple-500 p-3">
                                <p class="text-sm font-medium text-purple-900">Reference ${idx + 1}</p>
                                <p class="text-sm text-purple-700 mt-1">${escapeHtml(JSON.stringify(citation, null, 2))}</p>
                            </div>
                        `).join('')}
                    </div>
                </div>
            </div>
        `;
        
        document.getElementById('grade-modal').classList.remove('hidden');
        
    } catch (error) {
        alert('Error loading grade details: ' + error.message);
    }
}

// Modal Controls
document.getElementById('close-modal').addEventListener('click', () => {
    document.getElementById('grade-modal').classList.add('hidden');
});

document.getElementById('grade-modal').addEventListener('click', (e) => {
    if (e.target.id === 'grade-modal') {
        document.getElementById('grade-modal').classList.add('hidden');
    }
});

// Reference Upload Modal
function openReferenceModal(assignmentId) {
    document.getElementById('reference-assignment-id').value = assignmentId;
    document.getElementById('reference-modal').classList.remove('hidden');
}

document.getElementById('close-reference-modal').addEventListener('click', () => {
    document.getElementById('reference-modal').classList.add('hidden');
});

document.getElementById('upload-reference-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const assignmentId = document.getElementById('reference-assignment-id').value;
    const fileInput = document.getElementById('reference-file');
    const file = fileInput.files[0];
    
    if (!file) {
        alert('Please select a file');
        return;
    }
    
    const formData = new FormData();
    formData.append('file', file);
    
    try {
        const response = await fetch(`${API_BASE_URL}/assignments/${assignmentId}/references`, {
            method: 'POST',
            body: formData
        });
        
        if (!response.ok) {
            throw new Error('Failed to upload reference');
        }
        
        const result = await response.json();
        alert(`Reference uploaded! ${result.chunks_created} chunks indexed.`);
        
        document.getElementById('reference-modal').classList.add('hidden');
        document.getElementById('upload-reference-form').reset();
        
    } catch (error) {
        alert('Error: ' + error.message);
    }
});

// Utility Functions
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Auto-refresh submissions every 10 seconds
setInterval(() => {
    const currentTab = document.querySelector('.tab-btn.active').id;
    if (currentTab === 'tab-submissions') {
        loadSubmissions();
    }
}, 10000);

// Initial Load
loadAssignments();
loadAssignmentsForDropdown();
