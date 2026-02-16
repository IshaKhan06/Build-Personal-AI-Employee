/**
 * Email MCP Server
 * Capabilities: draft and send emails via Gmail API with credentials.json
 * Draft function: save draft as .md in /Plans/email_draft_[date].md
 * Send function: only after HITL approval
 */

const fs = require('fs');
const path = require('path');
const { google } = require('googleapis');

// Initialize Express server
const express = require('express');
const app = express();
const port = process.env.PORT || 3000;

// Middleware
app.use(express.json());
app.use(express.urlencoded({ extended: true }));

// Gmail API setup
let oauth2Client = null;

// Initialize Gmail API client
function initializeGmailClient() {
  try {
    // Load credentials
    const credentialsPath = path.resolve('../..', 'client_secret_1093597334328-n5qe4i3r8l2a4csce2a018h9e2psmb56.apps.googleusercontent.com.json');
    
    if (!fs.existsSync(credentialsPath)) {
      console.warn(`Credentials file not found at ${credentialsPath}. Gmail functionality will be limited.`);
      return;
    }

    const credentials = JSON.parse(fs.readFileSync(credentialsPath));
    const { client_secret, client_id, redirect_uris } = credentials.installed;

    oauth2Client = new google.auth.OAuth2(
      client_id,
      client_secret,
      redirect_uris[0]
    );

    // Try to load token from file
    const tokenPath = path.resolve('../..', 'token.json');
    if (fs.existsSync(tokenPath)) {
      const token = JSON.parse(fs.readFileSync(tokenPath));
      oauth2Client.setCredentials(token);
    }

    console.log('Gmail API client initialized');
  } catch (error) {
    console.error('Error initializing Gmail API client:', error.message);
    console.warn('Gmail functionality will be limited.');
  }
}

// Function to save email draft as .md file in /Plans
function saveDraftAsMarkdown(emailData) {
  const plansDir = path.join(__dirname, '../../Plans');
  if (!fs.existsSync(plansDir)) {
    fs.mkdirSync(plansDir, { recursive: true });
  }

  const dateStr = new Date().toISOString().replace(/[:.]/g, '-').replace('T', '_').split('Z')[0];
  const fileName = `email_draft_${dateStr}.md`;
  const filePath = path.join(plansDir, fileName);

  // Create YAML frontmatter
  const yamlFrontmatter = `---
type: email_draft
to: "${emailData.to || ''}"
subject: "${emailData.subject || ''}"
status: pending_approval
priority: ${emailData.priority || 'medium'}
created: "${new Date().toISOString()}"
---
`;

  // Create markdown content
  const markdownContent = `${yamlFrontmatter}

## Email Draft

**To:** ${emailData.to || 'N/A'}

**Subject:** ${emailData.subject || 'N/A'}

**Priority:** ${emailData.priority || 'medium'}

### Body:
${emailData.body || ''}

---
*Draft created by Email MCP Server*
`;

  fs.writeFileSync(filePath, markdownContent);
  console.log(`Email draft saved to: ${filePath}`);
  return filePath;
}

// Endpoint to draft an email
app.post('/draft', async (req, res) => {
  try {
    const { to, subject, body, priority } = req.body;

    if (!to || !subject || !body) {
      return res.status(400).json({ 
        error: 'Missing required fields: to, subject, body' 
      });
    }

    // Save draft as markdown file
    const draftPath = saveDraftAsMarkdown({
      to,
      subject,
      body,
      priority: priority || 'medium'
    });

    res.json({
      success: true,
      message: 'Email draft created successfully',
      draftPath: draftPath
    });
  } catch (error) {
    console.error('Error creating email draft:', error);
    res.status(500).json({ 
      error: 'Failed to create email draft',
      details: error.message 
    });
  }
});

// Endpoint to send an email (only after HITL approval)
app.post('/send', async (req, res) => {
  try {
    const { to, subject, body, threadId } = req.body;

    if (!oauth2Client) {
      console.error('Gmail API client not initialized');
      return res.status(500).json({ 
        error: 'Gmail API client not initialized. Cannot send email.' 
      });
    }

    if (!to || !subject || !body) {
      return res.status(400).json({ 
        error: 'Missing required fields: to, subject, body' 
      });
    }

    // Create the email message
    const emailLines = [
      `To: ${to}`,
      `Subject: ${subject}`,
      '',
      body
    ];
    const emailRaw = Buffer.from(emailLines.join('\r\n')).toString('base64').replace(/\+/g, '-').replace(/\//g, '_');

    // Send the email
    const gmail = google.gmail({ version: 'v1', auth: oauth2Client });
    const response = await gmail.users.messages.send({
      userId: 'me',
      requestBody: {
        raw: emailRaw,
        threadId: threadId
      }
    });

    res.json({
      success: true,
      message: 'Email sent successfully',
      messageId: response.data.id
    });
  } catch (error) {
    console.error('Error sending email:', error);
    res.status(500).json({ 
      error: 'Failed to send email',
      details: error.message 
    });
  }
});

// Endpoint to list pending email drafts that need approval
app.get('/pending-drafts', (req, res) => {
  try {
    const plansDir = path.join(__dirname, '../../Plans');
    if (!fs.existsSync(plansDir)) {
      return res.json({ drafts: [] });
    }

    const files = fs.readdirSync(plansDir);
    const pendingDrafts = files
      .filter(file => file.startsWith('email_draft_') && file.endsWith('.md'))
      .map(file => {
        const filePath = path.join(plansDir, file);
        const content = fs.readFileSync(filePath, 'utf8');
        
        // Simple parsing of YAML frontmatter to get status
        const yamlMatch = content.match(/status:\s*(.+)/);
        const status = yamlMatch ? yamlMatch[1].trim() : 'unknown';
        
        return {
          fileName: file,
          filePath: filePath,
          status: status
        };
      })
      .filter(draft => draft.status === 'pending_approval'); // Only show drafts pending approval

    res.json({ drafts: pendingDrafts });
  } catch (error) {
    console.error('Error listing pending drafts:', error);
    res.status(500).json({ 
      error: 'Failed to list pending drafts',
      details: error.message 
    });
  }
});

// Endpoint to approve and send a draft
app.post('/approve-and-send/:fileName', async (req, res) => {
  try {
    const { fileName } = req.params;
    const plansDir = path.join(__dirname, '../../Plans');
    const filePath = path.join(plansDir, fileName);

    if (!fs.existsSync(filePath)) {
      return res.status(404).json({ 
        error: 'Draft file not found' 
      });
    }

    // Read the draft file
    const content = fs.readFileSync(filePath, 'utf8');
    
    // Parse the content to extract email details
    const toMatch = content.match(/to:\s*"([^"]*)"/);
    const subjectMatch = content.match(/subject:\s*"([^"]*)"/);
    const bodyStartIndex = content.indexOf('### Body:');
    
    if (!toMatch || !subjectMatch || bodyStartIndex === -1) {
      return res.status(400).json({ 
        error: 'Invalid draft format' 
      });
    }

    const to = toMatch[1];
    const subject = subjectMatch[1];
    const body = content.substring(bodyStartIndex + 9).trim(); // 9 is length of '### Body:'

    // Update the status in the file to 'sent'
    const updatedContent = content.replace(/status:\s*pending_approval/, 'status: sent');
    fs.writeFileSync(filePath, updatedContent);

    // Send the email via Gmail API
    if (!oauth2Client) {
      console.error('Gmail API client not initialized');
      return res.status(500).json({ 
        error: 'Gmail API client not initialized. Cannot send email.' 
      });
    }

    const emailLines = [
      `To: ${to}`,
      `Subject: ${subject}`,
      '',
      body
    ];
    const emailRaw = Buffer.from(emailLines.join('\r\n')).toString('base64').replace(/\+/g, '-').replace(/\//g, '_');

    const gmail = google.gmail({ version: 'v1', auth: oauth2Client });
    const response = await gmail.users.messages.send({
      userId: 'me',
      requestBody: {
        raw: emailRaw
      }
    });

    res.json({
      success: true,
      message: 'Email approved and sent successfully',
      messageId: response.data.id
    });
  } catch (error) {
    console.error('Error approving and sending email:', error);
    res.status(500).json({ 
      error: 'Failed to approve and send email',
      details: error.message 
    });
  }
});

// Health check endpoint
app.get('/', (req, res) => {
  res.json({ 
    status: 'Email MCP Server is running',
    capabilities: ['draft', 'send (with approval)', 'list pending drafts', 'approve and send'],
    timestamp: new Date().toISOString()
  });
});

// Initialize the Gmail client and start the server
initializeGmailClient();

app.listen(port, () => {
  console.log(`Email MCP Server listening at http://localhost:${port}`);
  console.log('Available endpoints:');
  console.log('  POST /draft - Create email draft');
  console.log('  POST /send - Send email (requires approval)');
  console.log('  GET  /pending-drafts - List pending drafts');
  console.log('  POST /approve-and-send/:fileName - Approve and send a draft');
});

module.exports = app;