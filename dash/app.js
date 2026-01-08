/**
 * LEGATO Dashboard
 * Monitors the Legato system across repositories
 */

const REPOS = {
    conduct: 'Legato.Conduct',
    library: 'Legato.Library',
    listen: 'Legato.Listen'
};

// Get config from inputs
function getConfig() {
    return {
        org: document.getElementById('org').value || 'bobbyhiddn',
        token: document.getElementById('token').value || null
    };
}

// GitHub API helper
async function githubFetch(endpoint) {
    const config = getConfig();
    const headers = {
        'Accept': 'application/vnd.github+json'
    };

    if (config.token) {
        headers['Authorization'] = `Bearer ${config.token}`;
    }

    const response = await fetch(`https://api.github.com${endpoint}`, { headers });

    if (!response.ok) {
        throw new Error(`GitHub API error: ${response.status}`);
    }

    return response.json();
}

// Format relative time
function timeAgo(dateString) {
    const date = new Date(dateString);
    const now = new Date();
    const seconds = Math.floor((now - date) / 1000);

    if (seconds < 60) return 'just now';
    if (seconds < 3600) return `${Math.floor(seconds / 60)}m ago`;
    if (seconds < 86400) return `${Math.floor(seconds / 3600)}h ago`;
    return `${Math.floor(seconds / 86400)}d ago`;
}

// Render system status
async function renderSystemStatus() {
    const container = document.getElementById('system-status');
    const config = getConfig();

    const statuses = [];

    for (const [key, repoName] of Object.entries(REPOS)) {
        try {
            const runs = await githubFetch(`/repos/${config.org}/${repoName}/actions/runs?per_page=1`);
            const latestRun = runs.workflow_runs[0];

            let status = 'success';
            let statusText = 'Operational';

            if (latestRun) {
                if (latestRun.status === 'in_progress' || latestRun.status === 'queued') {
                    status = 'loading';
                    statusText = 'Running';
                } else if (latestRun.conclusion === 'failure') {
                    status = 'error';
                    statusText = 'Failed';
                } else if (latestRun.conclusion === 'cancelled') {
                    status = 'warning';
                    statusText = 'Cancelled';
                }
            }

            statuses.push({ name: repoName, status, statusText });
        } catch (e) {
            statuses.push({ name: repoName, status: 'error', statusText: 'Unavailable' });
        }
    }

    container.innerHTML = statuses.map(s => `
        <div class="status-item ${s.status}">
            <span class="indicator"></span>
            <span>${s.name}: ${s.statusText}</span>
        </div>
    `).join('');
}

// Render statistics
async function renderStats() {
    const config = getConfig();

    // Count transcripts (workflow runs)
    try {
        const runs = await githubFetch(`/repos/${config.org}/${REPOS.conduct}/actions/workflows/process-transcript.yml/runs?per_page=100`);
        document.getElementById('stat-transcripts').textContent = runs.total_count || 0;
    } catch (e) {
        document.getElementById('stat-transcripts').textContent = '-';
    }

    // Count artifacts (files in Library)
    try {
        const contents = await githubFetch(`/repos/${config.org}/${REPOS.library}/contents`);
        const artifactDirs = contents.filter(c => c.type === 'dir' && !c.name.startsWith('.'));
        let artifactCount = 0;

        for (const dir of artifactDirs) {
            try {
                const files = await githubFetch(`/repos/${config.org}/${REPOS.library}/contents/${dir.name}`);
                artifactCount += files.filter(f => f.name.endsWith('.md')).length;
            } catch (e) {
                // Ignore errors for individual directories
            }
        }

        document.getElementById('stat-artifacts').textContent = artifactCount;
    } catch (e) {
        document.getElementById('stat-artifacts').textContent = '-';
    }

    // Count projects (Lab repos)
    try {
        const repos = await githubFetch(`/users/${config.org}/repos?per_page=100`);
        const labRepos = repos.filter(r => r.name.startsWith('Lab.'));
        document.getElementById('stat-projects').textContent = labRepos.length;
    } catch (e) {
        document.getElementById('stat-projects').textContent = '-';
    }
}

// Build tree view for a job
function buildJobTree(jobs) {
    if (!jobs || jobs.length === 0) {
        return '<p class="empty">No job details available</p>';
    }

    let html = '<div class="tree">';

    for (const job of jobs) {
        const icon = job.conclusion === 'success' ? '&#x2705;' :
                     job.conclusion === 'failure' ? '&#x274C;' :
                     job.status === 'in_progress' ? '&#x1F504;' : '&#x23F3;';

        const statusClass = job.conclusion === 'success' ? 'success' :
                           job.conclusion === 'failure' ? 'failure' :
                           job.status === 'in_progress' ? 'running' : 'pending';

        html += `
            <div class="tree-item tree-root">
                <span class="tree-icon">${icon}</span>
                <span class="tree-value ${statusClass}">${job.name}</span>
            </div>
        `;

        // Add steps as children
        if (job.steps && job.steps.length > 0) {
            for (const step of job.steps) {
                if (step.name.toLowerCase().includes('checkout') ||
                    step.name.toLowerCase().includes('setup python') ||
                    step.name.toLowerCase().includes('install')) {
                    continue; // Skip boilerplate steps
                }

                const stepIcon = step.conclusion === 'success' ? '&#x2705;' :
                                step.conclusion === 'failure' ? '&#x274C;' :
                                step.status === 'in_progress' ? '&#x1F504;' : '&#x23F3;';

                html += `
                    <div class="tree-item">
                        <span class="tree-icon">${stepIcon}</span>
                        <span class="tree-label">${step.name}</span>
                    </div>
                `;
            }
        }
    }

    html += '</div>';
    return html;
}

// Render transcript jobs
async function renderTranscriptJobs() {
    const container = document.getElementById('transcript-jobs');
    const config = getConfig();

    try {
        // Get recent workflow runs from Conduct
        const runs = await githubFetch(`/repos/${config.org}/${REPOS.conduct}/actions/workflows/process-transcript.yml/runs?per_page=5`);

        if (!runs.workflow_runs || runs.workflow_runs.length === 0) {
            container.innerHTML = '<p class="empty">No transcript jobs found</p>';
            return;
        }

        let html = '';

        for (const run of runs.workflow_runs) {
            const statusClass = run.conclusion === 'success' ? 'success' :
                               run.conclusion === 'failure' ? 'failure' :
                               run.status === 'in_progress' ? 'running' : 'pending';

            const statusText = run.conclusion || run.status;

            // Get job details for this run
            let treeHtml = '<p class="loading">Loading details...</p>';
            try {
                const jobs = await githubFetch(`/repos/${config.org}/${REPOS.conduct}/actions/runs/${run.id}/jobs`);
                treeHtml = buildJobTree(jobs.jobs);
            } catch (e) {
                treeHtml = '<p class="empty">Could not load job details</p>';
            }

            html += `
                <div class="job">
                    <div class="job-header">
                        <div>
                            <span class="job-title">${run.display_title || run.name}</span>
                            <span class="job-time">${timeAgo(run.created_at)}</span>
                        </div>
                        <span class="job-status ${statusClass}">${statusText}</span>
                    </div>
                    ${treeHtml}
                    <div style="margin-top: 0.5rem;">
                        <a href="${run.html_url}" target="_blank" style="font-size: 0.75rem;">View on GitHub &rarr;</a>
                    </div>
                </div>
            `;
        }

        container.innerHTML = html;
    } catch (e) {
        container.innerHTML = `<p class="empty">Error loading jobs: ${e.message}</p>`;
    }
}

// Render library artifacts
async function renderLibraryArtifacts() {
    const container = document.getElementById('library-artifacts');
    const config = getConfig();

    try {
        const commits = await githubFetch(`/repos/${config.org}/${REPOS.library}/commits?per_page=10`);

        if (!commits || commits.length === 0) {
            container.innerHTML = '<p class="empty">No artifacts found</p>';
            return;
        }

        // Get unique files from recent commits
        const artifacts = [];
        const seenFiles = new Set();

        for (const commit of commits) {
            if (artifacts.length >= 5) break;

            try {
                const details = await githubFetch(`/repos/${config.org}/${REPOS.library}/commits/${commit.sha}`);

                for (const file of (details.files || [])) {
                    if (file.filename.endsWith('.md') &&
                        !file.filename.includes('README') &&
                        !seenFiles.has(file.filename)) {

                        seenFiles.add(file.filename);

                        // Extract category from path
                        const parts = file.filename.split('/');
                        const category = parts.length > 1 ? parts[0] : 'unknown';
                        const name = parts[parts.length - 1].replace('.md', '');

                        artifacts.push({
                            name,
                            category,
                            path: file.filename,
                            date: commit.commit.author.date
                        });

                        if (artifacts.length >= 5) break;
                    }
                }
            } catch (e) {
                // Ignore individual commit errors
            }
        }

        if (artifacts.length === 0) {
            container.innerHTML = '<p class="empty">No artifacts found</p>';
            return;
        }

        container.innerHTML = `
            <ul class="item-list">
                ${artifacts.map(a => `
                    <li>
                        <div>
                            <span class="item-name">${a.name}</span>
                            <span class="item-meta">${timeAgo(a.date)}</span>
                        </div>
                        <span class="badge ${a.category}">${a.category}</span>
                    </li>
                `).join('')}
            </ul>
        `;
    } catch (e) {
        container.innerHTML = `<p class="empty">Error: ${e.message}</p>`;
    }
}

// Render lab projects
async function renderLabProjects() {
    const container = document.getElementById('lab-projects');
    const config = getConfig();

    try {
        const repos = await githubFetch(`/users/${config.org}/repos?per_page=100&sort=updated`);
        const labRepos = repos.filter(r => r.name.startsWith('Lab.')).slice(0, 5);

        if (labRepos.length === 0) {
            container.innerHTML = '<p class="empty">No Lab projects found</p>';
            return;
        }

        const projects = [];

        for (const repo of labRepos) {
            // Determine project type from name
            const isChord = repo.name.includes('.Chord');
            const isNote = repo.name.includes('.Note');
            const projectType = isChord ? 'chord' : isNote ? 'note' : 'unknown';

            // Check for open issues (waiting for auth)
            let hasOpenIssues = false;
            try {
                const issues = await githubFetch(`/repos/${config.org}/${repo.name}/issues?state=open&per_page=1`);
                hasOpenIssues = issues.length > 0;
            } catch (e) {
                // Ignore
            }

            projects.push({
                name: repo.name.replace('Lab.', ''),
                fullName: repo.name,
                type: projectType,
                status: hasOpenIssues ? 'waiting' : 'active',
                url: repo.html_url,
                updated: repo.updated_at
            });
        }

        container.innerHTML = `
            <ul class="item-list">
                ${projects.map(p => `
                    <li>
                        <div>
                            <a href="${p.url}" target="_blank" class="item-name">${p.name}</a>
                            <span class="item-meta">${timeAgo(p.updated)}</span>
                        </div>
                        <div>
                            <span class="badge ${p.type}">${p.type}</span>
                            <span class="badge ${p.status}">${p.status === 'waiting' ? 'awaiting' : 'active'}</span>
                        </div>
                    </li>
                `).join('')}
            </ul>
        `;
    } catch (e) {
        container.innerHTML = `<p class="empty">Error: ${e.message}</p>`;
    }
}

// Refresh all data
async function refreshAll() {
    document.getElementById('last-updated').textContent = 'Refreshing...';

    await Promise.all([
        renderSystemStatus(),
        renderStats(),
        renderTranscriptJobs(),
        renderLibraryArtifacts(),
        renderLabProjects()
    ]);

    document.getElementById('last-updated').textContent = new Date().toLocaleString();
}

// Initialize on load
document.addEventListener('DOMContentLoaded', () => {
    // Load saved org from localStorage
    const savedOrg = localStorage.getItem('legato-org');
    if (savedOrg) {
        document.getElementById('org').value = savedOrg;
    }

    // Save org on change
    document.getElementById('org').addEventListener('change', (e) => {
        localStorage.setItem('legato-org', e.target.value);
    });

    // Initial load
    refreshAll();

    // Auto-refresh every 60 seconds
    setInterval(refreshAll, 60000);
});
