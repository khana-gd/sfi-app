import React, { useState, useEffect } from 'react';
import { api } from './services/api';
import type { User, Assignment } from './services/api';
import { 
  BookOpen, 
  Calendar, 
  Bell, 
  MessageSquare, 
  LogOut, 
  User as UserIcon, 
  Users, 
  FolderPlus, 
  CheckCircle, 
  Clock, 
  HelpCircle,
  Sparkles,
  Search,
  FileText,
  AlertCircle,
  Palette,
  Upload,
  AlertTriangle
} from 'lucide-react';

interface Submission {
  id: number;
  assignment_id: number;
  student_id: number;
  submitted_at: string;
  status: string;
  submission_text?: string;
  file_url?: string;
}

interface Issue {
  id: number;
  student_id: number;
  assignment_id?: number;
  faculty_id: number;
  category: string;
  description: string;
  status: string;
  escalation_level: number;
  created_at: string;
  messages: Array<{
    id: number;
    sender_id?: number;
    content: string;
    is_ai_response: boolean;
    created_at: string;
  }>;
}

export default function App() {
  const [token, setToken] = useState<string | null>(api.getToken());
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<'DASHBOARD' | 'CHAT' | 'RESEARCH' | 'STUDIO' | 'PORTFOLIO'>('DASHBOARD');

  // Chat/WebSocket states
  const [chatMessages, setChatMessages] = useState<Array<{ id?: number; sender_id: number; content: string; created_at: string }>>([]);
  const [chatInput, setChatInput] = useState('');
  const [recipientId, setRecipientId] = useState<number | null>(null);
  const [ws, setWs] = useState<WebSocket | null>(null);
  const [partnerTyping, setPartnerTyping] = useState(false);
  const [chatError, setChatError] = useState('');
  const [wsReadyState, setWsReadyState] = useState<number>(WebSocket.CONNECTING);
  // Form states
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loginError, setLoginError] = useState('');

  // Academic list states
  const [assignments, setAssignments] = useState<Assignment[]>([]);
  const [submissions, setSubmissions] = useState<Submission[]>([]);
  const [issues, setIssues] = useState<Issue[]>([]);
  const [usersList, setUsersList] = useState<User[]>([]);

  // Selection & Modal states
  const [selectedAssignment, setSelectedAssignment] = useState<Assignment | null>(null);
  const [selectedSubmission, setSelectedSubmission] = useState<Submission | null>(null);
  const [selectedIssue, setSelectedIssue] = useState<Issue | null>(null);

  // Submission form states
  const [submissionText, setSubmissionText] = useState('');
  const [submissionSuccess, setSubmissionSuccess] = useState('');

  // Feedback form states
  const [feedbackText, setFeedbackText] = useState('');
  const [feedbackGrade, setFeedbackGrade] = useState('');
  const [feedbackSuccess, setFeedbackSuccess] = useState('');

  // Help Ticket form states
  const [issueCategory, setIssueCategory] = useState('INSTRUCTION_HELP');
  const [issueDesc, setIssueDesc] = useState('');
  const [issueSuccess, setIssueSuccess] = useState('');
  const [issueMessageText, setIssueMessageText] = useState('');
  const [issueDraft, setIssueDraft] = useState('');

  // Fashion Research states
  const [researchQuery, setResearchQuery] = useState('');
  const [researchResult, setResearchResult] = useState<{ query: string; grounded_text: string; citations: Array<{ index: number; title: string; url: string }> } | null>(null);
  const [researchLoading, setResearchLoading] = useState(false);
  const [attachedDriveFile, setAttachedDriveFile] = useState<{ id: string; name: string } | null>(null);

  // Design Studio states
  const [projects, setProjects] = useState<any[]>([]);
  const [selectedProject, setSelectedProject] = useState<any>(null);
  const [moodboards, setMoodboards] = useState<any[]>([]);
  const [selectedMoodboard, setSelectedMoodboard] = useState<any>(null);
  const [newProjectName, setNewProjectName] = useState('');
  const [newMoodboardName, setNewMoodboardName] = useState('');
  const [studioSilhouette, setStudioSilhouette] = useState('Lehenga');
  const [studioFabric, setStudioFabric] = useState('Velvet');
  const [studioColors, setStudioColors] = useState('Navy Blue & Gold');
  const [studioEmbroidery, setStudioEmbroidery] = useState('Zardozi motifs');
  const [generatingConcept, setGeneratingConcept] = useState(false);
  const [sketchFile, setSketchFile] = useState<File | null>(null);
  const [sketchAnalysis, setSketchAnalysis] = useState<any>(null);
  const [analyzingSketch, setAnalyzingSketch] = useState(false);
  const [refUrl, setRefUrl] = useState('');
  const [refTitle, setRefTitle] = useState('');
  const [refCaption, setRefCaption] = useState('');
  const [refImgUrl, setRefImgUrl] = useState('');


  // Portfolio states
  const [portfolioItems, setPortfolioItems] = useState<any[]>([]);
  const [selectedPortfolioCategory, setSelectedPortfolioCategory] = useState('ALL');
  const [portfolioTitle, setPortfolioTitle] = useState('');
  const [portfolioCategory, setPortfolioCategory] = useState('ILLUSTRATION');
  const [portfolioDesc, setPortfolioDesc] = useState('');
  const [portfolioFileUrl, setPortfolioFileUrl] = useState('');
  const [selectedPortfolioStudentId, setSelectedPortfolioStudentId] = useState<number | null>(null);

  // Analytics states
  const [studentAnalytics, setStudentAnalytics] = useState<any>(null);
  const [facultyWarnings, setFacultyWarnings] = useState<any[]>([]);

  // Create Assignment states
  const [newTitle, setNewTitle] = useState('');
  const [newDesc, setNewDesc] = useState('');
  const [newDeadline, setNewDeadline] = useState('');
  const [newPriority, setNewPriority] = useState('MEDIUM');
  const [newCategory, setNewCategory] = useState('');
  const [newGrading, setNewGrading] = useState('');
  const [assignmentSuccess, setAssignmentSuccess] = useState('');

  // Create User states
  const [createEmail, setCreateEmail] = useState('');
  const [createPassword, setCreatePassword] = useState('');
  const [createFirstName, setCreateFirstName] = useState('');
  const [createLastName, setCreateLastName] = useState('');
  const [createRole, setCreateRole] = useState('STUDENT');
  const [createUserSuccess, setCreateUserSuccess] = useState('');

  useEffect(() => {
    if (token) {
      fetchUserData();
    } else {
      setLoading(false);
    }
  }, [token]);

  useEffect(() => {
    if (activeTab === 'CHAT' && user) {
      if (user.role === 'STUDENT') {
        setRecipientId(2); // Faculty is user_id 2
      } else if (user.role === 'FACULTY') {
        setRecipientId(3); // Student 1 is user_id 3
      }
      connectWebSocket();
    } else {
      if (ws) {
        ws.close();
        setWs(null);
      }
    }
    return () => {
      if (ws) {
        ws.close();
      }
    };
  }, [activeTab, recipientId, user]);
  useEffect(() => {
    if (activeTab === 'CHAT' && recipientId) {
      fetchChatHistory();
    }
  }, [activeTab, recipientId]);

  const fetchChatHistory = async () => {
    try {
      const messages = await api.request(`/chat/messages/${recipientId}`);
      setChatMessages(messages);
    } catch (err: any) {
      console.error("Failed to load chat history:", err);
    }
  };

  useEffect(() => {
    if (selectedIssue && selectedIssue.escalation_level === 2 && user?.role === 'FACULTY') {
      fetchIssueDraft(selectedIssue.id);
    } else {
      setIssueDraft('');
    }
  }, [selectedIssue, user]);

  const fetchIssueDraft = async (issueId: number) => {
    try {
      const res = await api.request(`/issues/${issueId}/draft`);
      setIssueDraft(res.draft);
    } catch (err) {
      console.error("Failed to fetch AI draft suggestion:", err);
    }
  };

  const handleEscalateIssue = async (issueId: number) => {
    try {
      const updated = await api.request(`/issues/${issueId}/escalate`, { method: "POST" });
      setSelectedIssue(updated);
      setIssues(prev => prev.map(i => i.id === issueId ? updated : i));
    } catch (err: any) {
      console.error("Failed to escalate issue:", err);
    }
  };

  const handleSendDraft = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedIssue || !issueDraft) return;
    try {
      const msg = await api.request(`/issues/${selectedIssue.id}/messages`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({ content: issueDraft })
      });
      setSelectedIssue(prev => prev ? { ...prev, messages: [...prev.messages, msg] } : null);
      setIssues(prev => prev.map(i => i.id === selectedIssue.id ? { ...i, messages: [...i.messages, msg] } : i));
      setIssueDraft('');
    } catch (err) {
      console.error("Failed to send draft reply:", err);
    }
  };

  const handleResearchQuery = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!researchQuery.trim()) return;
    setResearchLoading(true);
    try {
      const res = await api.request("/research/query", {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({ query: researchQuery })
      });
      setResearchResult(res);
    } catch (err) {
      console.error("Failed to run grounded research query:", err);
    } finally {
      setResearchLoading(false);
    }
  };
  // Design Studio API requests & handlers
  useEffect(() => {
    if (activeTab === 'STUDIO' && user?.role === 'STUDENT') {
      fetchProjects();
    }
  }, [activeTab, user]);

  const fetchProjects = async () => {
    try {
      const data = await api.request("/design-studio/projects");
      setProjects(data);
      if (data.length > 0) {
        setSelectedProject(data[0]);
        fetchProjectMoodboards(data[0].id);
      }
    } catch (err) {
      console.error("Failed to load design studio projects:", err);
    }
  };

  const fetchProjectMoodboards = async (projectId: number) => {
    try {
      const mbs = await api.request(`/design-studio/projects/${projectId}/moodboards`);
      setMoodboards(mbs);
      if (mbs.length > 0) {
        // Load first moodboard detail (including items)
        const mbData = await api.request(`/design-studio/moodboards/${mbs[0].id}`);
        setSelectedMoodboard(mbData);
      } else {
        setSelectedMoodboard(null);
      }
    } catch (err) {
      console.error("Failed to fetch project moodboards:", err);
    }
  };

  const handleSelectProject = (proj: any) => {
    setSelectedProject(proj);
    fetchProjectMoodboards(proj.id);
  };

  const handleSelectMoodboard = async (mb: any) => {
    try {
      const mbData = await api.request(`/design-studio/moodboards/${mb.id}`);
      setSelectedMoodboard(mbData);
    } catch (err) {
      console.error("Failed to load moodboard details:", err);
    }
  };

  const handleCreateProject = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newProjectName.trim()) return;
    try {
      const data = await api.request("/design-studio/projects", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name: newProjectName })
      });
      setProjects(prev => [...prev, data]);
      setSelectedProject(data);
      setNewProjectName('');
      fetchProjectMoodboards(data.id);
    } catch (err) {
      console.error("Failed to create project:", err);
    }
  };

  const handleCreateMoodboard = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedProject || !newMoodboardName.trim()) return;
    try {
      const data = await api.request("/design-studio/moodboards", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ project_id: selectedProject.id, name: newMoodboardName })
      });
      setMoodboards(prev => [...prev, data]);
      setSelectedMoodboard(data);
      setNewMoodboardName('');
      // Reload moodboard detail
      const mbData = await api.request(`/design-studio/moodboards/${data.id}`);
      setSelectedMoodboard(mbData);
    } catch (err) {
      console.error("Failed to create moodboard:", err);
    }
  };

  const handleGenerateConcept = async (e: React.FormEvent) => {
    e.preventDefault();
    setGeneratingConcept(true);
    try {
      const formData = new FormData();
      formData.append("silhouette", studioSilhouette);
      formData.append("fabric", studioFabric);
      formData.append("colors", studioColors);
      formData.append("embroidery", studioEmbroidery);
      if (selectedMoodboard) {
        formData.append("moodboard_id", selectedMoodboard.id.toString());
      }
      await api.request("/design-studio/concept", {
        method: "POST",
        body: formData
      });
      if (selectedMoodboard) {
        const mbData = await api.request(`/design-studio/moodboards/${selectedMoodboard.id}`);
        setSelectedMoodboard(mbData);
      }
    } catch (err) {
      console.error("Failed to generate concept image:", err);
    } finally {
      setGeneratingConcept(false);
    }
  };

  const handleUploadSketch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!sketchFile) return;
    setAnalyzingSketch(true);
    try {
      const formData = new FormData();
      formData.append("file", sketchFile);
      if (selectedMoodboard) {
        formData.append("moodboard_id", selectedMoodboard.id.toString());
      }
      const data = await api.request("/design-studio/sketch/analyze", {
        method: "POST",
        body: formData
      });
      setSketchAnalysis(data);
      if (selectedMoodboard) {
        const mbData = await api.request(`/design-studio/moodboards/${selectedMoodboard.id}`);
        setSelectedMoodboard(mbData);
      }
    } catch (err) {
      console.error("Failed to analyze sketch:", err);
    } finally {
      setAnalyzingSketch(false);
    }
  };

  const handleAddReferenceItem = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedMoodboard || !refImgUrl.trim() || !refUrl.trim() || !refTitle.trim()) return;
    try {
      await api.request(`/design-studio/moodboards/${selectedMoodboard.id}/items`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          item_type: "REFERENCE_IMAGE",
          file_url: refImgUrl,
          caption: refCaption,
          source_url: refUrl,
          source_title: refTitle
        })
      });
      const mbData = await api.request(`/design-studio/moodboards/${selectedMoodboard.id}`);
      setSelectedMoodboard(mbData);
      setRefImgUrl('');
      setRefUrl('');
      setRefTitle('');
      setRefCaption('');
    } catch (err) {
      console.error("Failed to add reference image item:", err);
    }
  };

  // Portfolio handlers & effects
  useEffect(() => {
    if (activeTab === 'PORTFOLIO' && user) {
      if (user.role === 'STUDENT') {
        fetchPortfolioItems();
      } else {
        // Faculty selects Student 1 (profile ID 1) by default
        setSelectedPortfolioStudentId(1);
      }
    }
  }, [activeTab, user]);

  const fetchPortfolioItems = async (studentId?: number) => {
    try {
      const url = studentId ? `/portfolio/items?student_id=${studentId}` : "/portfolio/items";
      const data = await api.request(url);
      setPortfolioItems(data);
    } catch (err) {
      console.error("Failed to load portfolio items:", err);
    }
  };

  const handleCreatePortfolioItem = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!portfolioTitle.trim() || !portfolioFileUrl.trim()) return;
    try {
      await api.request("/portfolio/items", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          title: portfolioTitle,
          category: portfolioCategory,
          description: portfolioDesc,
          file_url: portfolioFileUrl
        })
      });
      setPortfolioTitle('');
      setPortfolioDesc('');
      setPortfolioFileUrl('');
      fetchPortfolioItems();
    } catch (err) {
      console.error("Failed to add portfolio item:", err);
    }
  };

  const handleDeletePortfolioItem = async (itemId: number) => {
    try {
      await api.request(`/portfolio/items/${itemId}`, { method: "DELETE" });
      fetchPortfolioItems(selectedPortfolioStudentId || undefined);
    } catch (err) {
      console.error("Failed to delete portfolio item:", err);
    }
  };

  const handleCompilePortfolio = () => {
    const studentId = selectedPortfolioStudentId || 1; // student 1 default
    const token = api.getToken();
    window.open(`http://localhost:8000/api/v1/portfolio/export/pdf?student_id=${studentId}&token=${token}`, "_blank");
  };

  // Analytics handlers & effects
  useEffect(() => {
    if (activeTab === 'DASHBOARD' && user) {
      if (user.role === 'STUDENT') {
        fetchStudentAnalytics();
      } else {
        fetchFacultyWarnings();
      }
    }
  }, [activeTab, user]);

  const fetchStudentAnalytics = async () => {
    try {
      const data = await api.request("/analytics/student/progress");
      setStudentAnalytics(data);
    } catch (err) {
      console.error("Failed to load student progress analytics:", err);
    }
  };

  const fetchFacultyWarnings = async () => {
    try {
      const data = await api.request("/analytics/faculty/warnings");
      setFacultyWarnings(data);
    } catch (err) {
      console.error("Failed to load faculty warnings list:", err);
    }
  };

  const connectWebSocket = async () => {
    try {
      setChatError('');
      setWsReadyState(WebSocket.CONNECTING);
      const ticketRes = await api.request("/auth/ws-ticket", { method: "POST" });
      const ticket = ticketRes.ticket;

      const socket = new WebSocket(`ws://localhost:8000/api/v1/chat/ws?ticket=${ticket}`);
      
      socket.onopen = () => {
        console.log("WebSocket connected");
        setWsReadyState(WebSocket.OPEN);
      };

      socket.onmessage = (event) => {
        const data = JSON.parse(event.data);
        if (data.type === 'MESSAGE') {
          setChatMessages(prev => {
            if (data.id && prev.some(m => m.id === data.id)) {
              return prev;
            }
            return [...prev, {
              id: data.id,
              sender_id: data.sender_id,
              content: data.content,
              created_at: data.created_at
            }];
          });
        } else if (data.type === 'TYPING') {
          setPartnerTyping(data.is_typing);
        } else if (data.type === 'ERROR') {
          setChatError(data.content);
        }
      };

      socket.onclose = () => {
        console.log("WebSocket disconnected");
        setWsReadyState(WebSocket.CLOSED);
      };

      socket.onerror = () => {
        setWsReadyState(WebSocket.CLOSED);
      };

      setWs(socket);
    } catch (err: any) {
      setChatError(`WebSocket error: ${err.message}`);
      setWsReadyState(WebSocket.CLOSED);
    }
  };

  const handleSendChatMessage = (e: React.FormEvent) => {
    e.preventDefault();
    if (!ws || ws.readyState !== WebSocket.OPEN || !chatInput || !recipientId || !user) return;
    
    ws.send(JSON.stringify({
      type: "SEND_MESSAGE",
      recipient_id: recipientId,
      content: chatInput
    }));

    setChatMessages(prev => [...prev, {
      sender_id: user.id,
      content: chatInput,
      created_at: new Date().toISOString()
    }]);

    setChatInput('');
  };

  const fetchUserData = async () => {
    try {
      setLoading(true);
      const currentUser = await api.getMe();
      setUser(currentUser);
      
      if (currentUser.role === 'ADMIN') {
        const uList = await api.getUsers();
        setUsersList(uList);
      } else {
        const aList = await api.getAssignments();
        setAssignments(aList);
        
        // Fetch submissions & issues
        const subList = await api.request("/submissions");
        setSubmissions(subList);

        const issueList = await api.request("/issues");
        setIssues(issueList);
      }
    } catch (err) {
      console.error(err);
      handleLogout();
    } finally {
      setLoading(false);
    }
  };

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoginError('');
    try {
      const data = await api.login(email, password);
      setToken(data.access_token);
    } catch (err: any) {
      setLoginError(err.message || 'Login failed. Please try again.');
    }
  };

  const handleLogout = () => {
    api.logout();
    setToken(null);
    setUser(null);
    setEmail('');
    setPassword('');
  };

  const handleCreateAssignment = async (e: React.FormEvent) => {
    e.preventDefault();
    setAssignmentSuccess('');
    try {
      await api.createAssignment({
        title: newTitle,
        description: newDesc,
        deadline: new Date(newDeadline).toISOString(),
        priority: newPriority,
        category: newCategory,
        grading_criteria: newGrading,
        drive_file_id: attachedDriveFile ? attachedDriveFile.id : null,
        drive_file_name: attachedDriveFile ? attachedDriveFile.name : null,
        drive_file_url: attachedDriveFile ? `https://drive.google.com/open?id=${attachedDriveFile.id}` : null
      });
      setAssignmentSuccess('Assignment published successfully!');
      setNewTitle('');
      setNewDesc('');
      setNewDeadline('');
      setNewCategory('');
      setNewGrading('');
      setAttachedDriveFile(null);
      
      // Reload
      const aList = await api.getAssignments();
      setAssignments(aList);
    } catch (err: any) {
      setAssignmentSuccess(`Error: ${err.message}`);
    }
  };

  const handleCreateUser = async (e: React.FormEvent) => {
    e.preventDefault();
    setCreateUserSuccess('');
    try {
      await api.createUser({
        email: createEmail,
        password: createPassword,
        first_name: createFirstName,
        last_name: createLastName,
        role: createRole
      });
      setCreateUserSuccess('User registered successfully!');
      setCreateEmail('');
      setCreatePassword('');
      setCreateFirstName('');
      setCreateLastName('');
      
      const uList = await api.getUsers();
      setUsersList(uList);
    } catch (err: any) {
      setCreateUserSuccess(`Error: ${err.message}`);
    }
  };

  const handleUploadSubmission = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedAssignment) return;
    setSubmissionSuccess('');
    try {
      const formData = new FormData();
      formData.append("assignment_id", selectedAssignment.id.toString());
      formData.append("submission_text", submissionText);

      const res = await fetch("http://localhost:8000/api/v1/submissions/", {
        method: "POST",
        headers: {
          "Authorization": `Bearer ${api.getToken()}`
        },
        body: formData
      });

      if (!res.ok) {
        throw new Error("Failed to upload submission");
      }

      setSubmissionSuccess("Work submitted successfully!");
      setSubmissionText('');
      
      // Refresh list
      const subList = await api.request("/submissions");
      setSubmissions(subList);
    } catch (err: any) {
      setSubmissionSuccess(`Error: ${err.message}`);
    }
  };

  const handlePostFeedback = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedSubmission) return;
    setFeedbackSuccess('');
    try {
      const payload = {
        feedback_text: feedbackText,
        grade: feedbackGrade
      };
      await api.request(`/submissions/${selectedSubmission.id}/feedback`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify(payload)
      });
      setFeedbackSuccess("Evaluation saved!");
      setFeedbackText('');
      setFeedbackGrade('');
      setTimeout(() => {
        setSelectedSubmission(null);
        setFeedbackSuccess('');
      }, 1000);

      // Refresh list
      const subList = await api.request("/submissions");
      setSubmissions(subList);
    } catch (err: any) {
      setFeedbackSuccess(`Error: ${err.message}`);
    }
  };

  const handleCreateIssue = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedAssignment) return;
    setIssueSuccess('');
    try {
      const payload = {
        assignment_id: selectedAssignment.id,
        category: issueCategory,
        description: issueDesc
      };
      await api.request("/issues/", {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify(payload)
      });
      setIssueSuccess("Help ticket created!");
      setIssueDesc('');
      
      // Refresh list
      const issueList = await api.request("/issues");
      setIssues(issueList);
    } catch (err: any) {
      setIssueSuccess(`Error: ${err.message}`);
    }
  };

  const handlePostIssueMessage = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedIssue) return;
    try {
      await api.request(`/issues/${selectedIssue.id}/messages`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({ content: issueMessageText })
      });
      setIssueMessageText('');
      
      // Refresh details
      const updated = await api.request(`/issues/${selectedIssue.id}`);
      setSelectedIssue(updated);
      
      // Refresh list
      const issueList = await api.request("/issues");
      setIssues(issueList);
    } catch (err) {
      console.error(err);
    }
  };

  if (loading) {
    return (
      <div style={{
        display: 'flex',
        height: '100vh',
        alignItems: 'center',
        justifyContent: 'center',
        backgroundColor: '#0B132B',
        color: '#F8F9FA'
      }}>
        <div style={{ textAlign: 'center' }}>
          <Sparkles style={{ animation: 'spin 2s linear infinite', color: '#C9A65B', width: 40, height: 40, marginBottom: 16 }} />
          <h2 style={{ fontFamily: 'var(--font-display)', fontWeight: 400 }}>Loading KANHA...</h2>
        </div>
      </div>
    );
  }

  // --- LOGIN PAGE ---
  if (!token || !user) {
    return (
      <div style={{
        display: 'flex',
        minHeight: '100vh',
        alignItems: 'center',
        justifyContent: 'center',
        backgroundColor: '#0B132B',
        padding: '24px'
      }}>
        <div className="card-glass" style={{ width: '100%', maxWidth: '440px', border: '1px solid var(--color-gold-primary)' }}>
          <div style={{ textAlign: 'center', marginBottom: '32px' }}>
            <div style={{ display: 'inline-flex', padding: '12px', background: 'rgba(201, 166, 91, 0.1)', borderRadius: '50%', marginBottom: '16px' }}>
              <Sparkles style={{ color: 'var(--color-gold-primary)', width: 32, height: 32 }} />
            </div>
            <h1 style={{ fontSize: '36px', color: 'var(--color-text-primary)', marginBottom: '8px' }}>KANHA</h1>
            <p style={{ color: 'var(--color-pink-accent)', textTransform: 'uppercase', fontSize: '11px', letterSpacing: '0.25em', fontWeight: 700 }}>
              AI-Powered Academic Companion
            </p>
          </div>

          {loginError && (
            <div style={{
              backgroundColor: 'rgba(255, 107, 107, 0.15)',
              border: '1px solid var(--color-error)',
              color: 'var(--color-error)',
              padding: '12px',
              borderRadius: '6px',
              fontSize: '14px',
              marginBottom: '20px'
            }}>
              {loginError}
            </div>
          )}

          <form onSubmit={handleLogin}>
            <div className="form-group">
              <label className="form-label">Institute Email</label>
              <input 
                type="email" 
                className="form-control" 
                placeholder="name@kanha.local"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
              />
            </div>
            <div className="form-group" style={{ marginBottom: '32px' }}>
              <label className="form-label">Password</label>
              <input 
                type="password" 
                className="form-control" 
                placeholder="••••••••"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
              />
            </div>
            <button type="submit" className="btn btn-primary" style={{ width: '100%', padding: '14px' }}>
              Sign In to Studio
            </button>
          </form>

          <div style={{ textAlign: 'center', marginTop: '24px', fontSize: '12px', color: 'var(--color-text-secondary)' }}>
            <p>Seeded accounts password is <strong>KanhaDevPass2026!</strong></p>
            <p style={{ marginTop: '8px' }}>
              student1@kanha.local | faculty@kanha.local | admin@kanha.local
            </p>
          </div>
        </div>
      </div>
    );
  }

  // --- APP LAYOUT (Logged In) ---
  return (
    <div className="app-container">
      {/* Sidebar Navigation */}
      <aside style={{
        position: 'fixed',
        left: 0,
        top: 0,
        bottom: 0,
        width: '260px',
        background: '#0B132B',
        borderRight: '1px solid var(--color-border)',
        display: 'flex',
        flexDirection: 'column',
        padding: '24px'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '40px' }}>
          <Sparkles style={{ color: 'var(--color-gold-primary)', width: 24, height: 24 }} />
          <div>
            <h2 style={{ fontSize: '24px', letterSpacing: '0.05em' }}>KANHA</h2>
            <span style={{ fontSize: '10px', textTransform: 'uppercase', letterSpacing: '0.15em', color: 'var(--color-pink-accent)', fontWeight: 700 }}>
              SFI Companion
            </span>
          </div>
        </div>

        <nav style={{ display: 'flex', flexDirection: 'column', gap: '8px', flex: 1 }}>
          <div 
            style={{
              display: 'flex', 
              alignItems: 'center', 
              gap: '12px', 
              padding: '12px 16px', 
              borderRadius: '8px',
              background: activeTab === 'DASHBOARD' ? 'rgba(201, 166, 91, 0.08)' : 'transparent',
              borderLeft: activeTab === 'DASHBOARD' ? '4px solid var(--color-gold-primary)' : '4px solid transparent',
              color: activeTab === 'DASHBOARD' ? 'var(--color-text-primary)' : 'var(--color-text-secondary)',
              cursor: 'pointer'
            }}
            onClick={() => setActiveTab('DASHBOARD')}
          >
            <BookOpen size={18} style={{ color: activeTab === 'DASHBOARD' ? 'var(--color-gold-primary)' : 'var(--color-text-secondary)' }} />
            <span style={{ fontWeight: 600, fontSize: '14px' }}>Dashboard</span>
          </div>
          
          <div 
            style={{
              display: 'flex', 
              alignItems: 'center', 
              gap: '12px', 
              padding: '12px 16px', 
              borderRadius: '8px',
              background: activeTab === 'RESEARCH' ? 'rgba(201, 166, 91, 0.08)' : 'transparent',
              borderLeft: activeTab === 'RESEARCH' ? '4px solid var(--color-gold-primary)' : '4px solid transparent',
              color: activeTab === 'RESEARCH' ? 'var(--color-text-primary)' : 'var(--color-text-secondary)',
              cursor: 'pointer'
            }}
            onClick={() => setActiveTab('RESEARCH')}
          >
            <Search size={18} style={{ color: activeTab === 'RESEARCH' ? 'var(--color-gold-primary)' : 'var(--color-text-secondary)' }} />
            <span style={{ fontSize: '14px', fontWeight: activeTab === 'RESEARCH' ? 600 : 400 }}>Fashion Research</span>
          </div>

          {user?.role === 'STUDENT' && (
            <div 
              style={{
                display: 'flex', 
                alignItems: 'center', 
                gap: '12px', 
                padding: '12px 16px', 
                borderRadius: '8px',
                background: activeTab === 'STUDIO' ? 'rgba(201, 166, 91, 0.08)' : 'transparent',
                borderLeft: activeTab === 'STUDIO' ? '4px solid var(--color-gold-primary)' : '4px solid transparent',
                color: activeTab === 'STUDIO' ? 'var(--color-text-primary)' : 'var(--color-text-secondary)',
                cursor: 'pointer'
              }}
              onClick={() => setActiveTab('STUDIO')}
            >
              <Palette size={18} style={{ color: activeTab === 'STUDIO' ? 'var(--color-gold-primary)' : 'var(--color-text-secondary)' }} />
              <span style={{ fontSize: '14px', fontWeight: activeTab === 'STUDIO' ? 600 : 400 }}>Design Studio</span>
            </div>
          )}
          
          {(user?.role === 'STUDENT' || user?.role === 'FACULTY') && (
            <div 
              style={{
                display: 'flex', 
                alignItems: 'center', 
                gap: '12px', 
                padding: '12px 16px', 
                borderRadius: '8px',
                background: activeTab === 'PORTFOLIO' ? 'rgba(201, 166, 91, 0.08)' : 'transparent',
                borderLeft: activeTab === 'PORTFOLIO' ? '4px solid var(--color-gold-primary)' : '4px solid transparent',
                color: activeTab === 'PORTFOLIO' ? 'var(--color-text-primary)' : 'var(--color-text-secondary)',
                cursor: 'pointer'
              }}
              onClick={() => setActiveTab('PORTFOLIO')}
            >
              <FolderPlus size={18} style={{ color: activeTab === 'PORTFOLIO' ? 'var(--color-gold-primary)' : 'var(--color-text-secondary)' }} />
              <span style={{ fontSize: '14px', fontWeight: activeTab === 'PORTFOLIO' ? 600 : 400 }}>Portfolio</span>
            </div>
          )}

          <div 
            style={{
              display: 'flex', 
              alignItems: 'center', 
              gap: '12px', 
              padding: '12px 16px', 
              borderRadius: '8px',
              background: activeTab === 'CHAT' ? 'rgba(201, 166, 91, 0.08)' : 'transparent',
              borderLeft: activeTab === 'CHAT' ? '4px solid var(--color-gold-primary)' : '4px solid transparent',
              color: activeTab === 'CHAT' ? 'var(--color-text-primary)' : 'var(--color-text-secondary)',
              cursor: 'pointer'
            }}
            onClick={() => setActiveTab('CHAT')}
          >
            <MessageSquare size={18} style={{ color: activeTab === 'CHAT' ? 'var(--color-gold-primary)' : 'var(--color-text-secondary)' }} />
            <span style={{ fontSize: '14px', fontWeight: activeTab === 'CHAT' ? 600 : 400 }}>KANHA Chat</span>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '12px', padding: '12px 16px', color: 'var(--color-text-secondary)', cursor: 'not-allowed' }}>
            <Bell size={18} />
            <span style={{ fontSize: '14px' }}>Notifications</span>
          </div>
        </nav>

        {/* User Card */}
        <div style={{
          borderTop: '1px solid var(--color-border)',
          paddingTop: '20px',
          display: 'flex',
          flexDirection: 'column',
          gap: '12px'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <div style={{ background: 'rgba(232, 159, 181, 0.1)', padding: '8px', borderRadius: '50%' }}>
              <UserIcon size={20} style={{ color: 'var(--color-pink-accent)' }} />
            </div>
            <div>
              <p style={{ fontWeight: 600, fontSize: '14px' }}>{user.first_name} {user.last_name}</p>
              <p style={{ fontSize: '11px', color: 'var(--color-pink-accent)', fontWeight: 700 }}>{user.role}</p>
            </div>
          </div>
          
          <button onClick={handleLogout} className="btn btn-secondary" style={{ width: '100%', gap: '8px', padding: '8px 16px' }}>
            <LogOut size={16} />
            Sign Out
          </button>
        </div>
      </aside>

      {/* Main Content Area */}
      <main className="main-content">

        {activeTab === 'RESEARCH' && (
          <div style={{ display: 'flex', flexDirection: 'column', minHeight: 'calc(100vh - 120px)' }}>
            <div style={{ marginBottom: '32px' }}>
              <h1 style={{ fontSize: '36px', color: 'var(--color-text-primary)' }}>Fashion Research Engine</h1>
              <p style={{ color: 'var(--color-pink-accent)', fontSize: '11px', textTransform: 'uppercase', letterSpacing: '0.2em', fontWeight: 700 }}>
                Grounded SFI Reference Assistant & Citation Directory
              </p>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 340px', gap: '32px' }}>
              {/* Query Panel & Results */}
              <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
                <div className="card-glass">
                  <form onSubmit={handleResearchQuery} style={{ display: 'flex', gap: '12px' }}>
                    <input 
                      type="text" 
                      className="form-control" 
                      placeholder="Ask KANHA about textiles, embroidery, historical silhouettes..."
                      value={researchQuery}
                      onChange={(e) => setResearchQuery(e.target.value)}
                      required
                    />
                    <button type="submit" className="btn btn-primary" style={{ padding: '0 24px' }} disabled={researchLoading}>
                      {researchLoading ? 'Searching...' : 'Search'}
                    </button>
                  </form>

                  {/* Suggestions list */}
                  <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap', marginTop: '16px' }}>
                    {['Mughal embroidery motifs', 'Lucknow Chikankari history', 'Banarasi brocade patterns', 'Draping crinoline silhouettes'].map((s) => (
                      <span 
                        key={s} 
                        style={{
                          fontSize: '11px', 
                          background: 'rgba(232, 159, 181, 0.1)', 
                          color: 'var(--color-pink-accent)', 
                          padding: '4px 10px', 
                          borderRadius: '12px', 
                          cursor: 'pointer',
                          fontWeight: 500
                        }}
                        onClick={() => { setResearchQuery(s); }}
                      >
                        {s}
                      </span>
                    ))}
                  </div>
                </div>

                {researchResult && (
                  <div className="card-glass" style={{ minHeight: '300px' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px', borderBottom: '1px solid var(--color-border)', paddingBottom: '12px' }}>
                      <h3 style={{ fontSize: '18px', color: 'var(--color-gold-primary)' }}>Research Findings</h3>
                      <button 
                        className="btn btn-secondary" 
                        style={{ fontSize: '12px', padding: '6px 12px' }}
                        onClick={async () => {
                          const exportRes = await api.request("/google/docs/export", {
                            method: "POST",
                            headers: { "Content-Type": "application/json" },
                            body: JSON.stringify({ title: researchResult.query, content_markdown: researchResult.grounded_text })
                          });
                          window.open(exportRes.google_doc_url, "_blank");
                        }}
                      >
                        Export to Google Docs
                      </button>
                    </div>

                    <div style={{ lineHeight: '1.6', fontSize: '15px', color: 'var(--color-text-primary)' }}>
                      {researchResult.grounded_text}
                    </div>
                  </div>
                )}
              </div>

              {/* Reference Citation Sidebar */}
              <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
                <div className="card-glass" style={{ height: '100%' }}>
                  <h3 style={{ fontSize: '14px', textTransform: 'uppercase', color: 'var(--color-text-secondary)', letterSpacing: '0.1em', marginBottom: '16px', borderBottom: '1px solid var(--color-border)', paddingBottom: '8px' }}>
                    Grounded Citations
                  </h3>
                  
                  {!researchResult || researchResult.citations.length === 0 ? (
                    <p style={{ color: 'var(--color-text-muted)', fontSize: '13px' }}>
                      Verified historical and material source cards will appear here during search.
                    </p>
                  ) : (
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
                      {researchResult.citations.map((c) => (
                        <div key={c.index} style={{
                          background: 'rgba(11, 19, 43, 0.4)',
                          border: '1px solid var(--color-border)',
                          borderRadius: '8px',
                          padding: '16px',
                          display: 'flex',
                          flexDirection: 'column',
                          gap: '6px'
                        }}>
                          <span style={{ fontSize: '10px', color: 'var(--color-pink-accent)', fontWeight: 700 }}>
                            SOURCE [{c.index}]
                          </span>
                          <strong style={{ fontSize: '14px', color: 'var(--color-text-primary)' }}>{c.title}</strong>
                          <a 
                            href={c.url} 
                            target="_blank" 
                            rel="noreferrer" 
                            style={{ fontSize: '12px', color: 'var(--color-gold-primary)', textDecoration: 'underline', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}
                          >
                            {c.url}
                          </a>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            </div>
          </div>
        )}

        {activeTab === 'STUDIO' && (
          <div style={{ display: 'flex', flexDirection: 'column', minHeight: 'calc(100vh - 120px)' }}>
            <div style={{ marginBottom: '32px' }}>
              <h1 style={{ fontSize: '36px', color: 'var(--color-text-primary)' }}>Fashion AI Design Studio</h1>
              <p style={{ color: 'var(--color-pink-accent)', fontSize: '11px', textTransform: 'uppercase', letterSpacing: '0.2em', fontWeight: 700 }}>
                Moodboards, Text-to-Design Generation & Multimodal Sketch Analysis
              </p>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '300px 1fr', gap: '32px', alignItems: 'start' }}>
              {/* Left Sidebar: Projects & Moodboards Management */}
              <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
                {/* Projects Section */}
                <div className="card-glass">
                  <h3 style={{ fontSize: '16px', color: 'var(--color-gold-primary)', marginBottom: '16px', borderBottom: '1px solid var(--color-border)', paddingBottom: '8px' }}>
                    Design Projects
                  </h3>
                  {projects.length === 0 ? (
                    <p style={{ fontSize: '13px', color: 'var(--color-text-secondary)', marginBottom: '16px' }}>No active projects.</p>
                  ) : (
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', marginBottom: '16px' }}>
                      {projects.map(p => (
                        <div 
                          key={p.id}
                          style={{
                            padding: '10px 14px',
                            borderRadius: '6px',
                            background: selectedProject?.id === p.id ? 'rgba(201, 166, 91, 0.12)' : 'rgba(11, 19, 43, 0.4)',
                            border: selectedProject?.id === p.id ? '1px solid var(--color-gold-primary)' : '1px solid var(--color-border)',
                            cursor: 'pointer',
                            fontSize: '14px',
                            fontWeight: selectedProject?.id === p.id ? 600 : 400
                          }}
                          onClick={() => handleSelectProject(p)}
                        >
                          {p.name}
                        </div>
                      ))}
                    </div>
                  )}

                  <form onSubmit={handleCreateProject} style={{ display: 'flex', gap: '8px' }}>
                    <input 
                      type="text" 
                      className="form-control" 
                      placeholder="New Project Name..." 
                      style={{ fontSize: '13px', padding: '6px 10px' }}
                      value={newProjectName}
                      onChange={(e) => setNewProjectName(e.target.value)}
                      required
                    />
                    <button type="submit" className="btn btn-primary" style={{ padding: '6px 12px', fontSize: '13px' }}>Create</button>
                  </form>
                </div>

                {/* Moodboards Section */}
                {selectedProject && (
                  <div className="card-glass">
                    <h3 style={{ fontSize: '16px', color: 'var(--color-pink-accent)', marginBottom: '16px', borderBottom: '1px solid var(--color-border)', paddingBottom: '8px' }}>
                      Moodboards
                    </h3>
                    {moodboards.length === 0 ? (
                      <p style={{ fontSize: '13px', color: 'var(--color-text-secondary)', marginBottom: '16px' }}>No moodboards created yet.</p>
                    ) : (
                      <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', marginBottom: '16px' }}>
                        {moodboards.map(m => (
                          <div 
                            key={m.id}
                            style={{
                              padding: '10px 14px',
                              borderRadius: '6px',
                              background: selectedMoodboard?.id === m.id ? 'rgba(232, 159, 181, 0.1)' : 'rgba(11, 19, 43, 0.4)',
                              border: selectedMoodboard?.id === m.id ? '1px solid var(--color-pink-accent)' : '1px solid var(--color-border)',
                              cursor: 'pointer',
                              fontSize: '14px',
                              fontWeight: selectedMoodboard?.id === m.id ? 600 : 400
                            }}
                            onClick={() => handleSelectMoodboard(m)}
                          >
                            📁 {m.name}
                          </div>
                        ))}
                      </div>
                    )}

                    <form onSubmit={handleCreateMoodboard} style={{ display: 'flex', gap: '8px' }}>
                      <input 
                        type="text" 
                        className="form-control" 
                        placeholder="New Moodboard..." 
                        style={{ fontSize: '13px', padding: '6px 10px' }}
                        value={newMoodboardName}
                        onChange={(e) => setNewMoodboardName(e.target.value)}
                        required
                      />
                      <button type="submit" className="btn btn-secondary" style={{ padding: '6px 12px', fontSize: '13px' }}>Add</button>
                    </form>
                  </div>
                )}
              </div>

              {/* Right Panel: Selected Moodboard View, AI Generation & Vision Analysis */}
              <div style={{ display: 'flex', flexDirection: 'column', gap: '32px' }}>
                
                {/* AI Design Tools: Generator & Sketch Analyzer */}
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '32px' }}>
                  
                  {/* Text-to-Design Generation Form */}
                  <div className="card-glass" style={{ background: 'rgba(28, 37, 65, 0.4)' }}>
                    <h3 style={{ fontSize: '18px', color: 'var(--color-gold-primary)', marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '8px' }}>
                      <Sparkles style={{ color: 'var(--color-gold-primary)', width: 18, height: 18 }} />
                      Text-to-Design Concept
                    </h3>
                    <form onSubmit={handleGenerateConcept} style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                      <div className="form-group">
                        <label className="form-label" style={{ fontSize: '12px' }}>Silhouette</label>
                        <select 
                          className="form-control" 
                          style={{ fontSize: '13px', padding: '6px 10px' }}
                          value={studioSilhouette}
                          onChange={(e) => setStudioSilhouette(e.target.value)}
                        >
                          <option value="Lehenga">Lehenga (Indian Bridal)</option>
                          <option value="Anarkali">Anarkali (Mughal-inspired)</option>
                          <option value="Sherwani">Sherwani (Traditional Men's)</option>
                          <option value="Saree">Saree (Banarasi silk drape)</option>
                        </select>
                      </div>
                      
                      <div className="form-group">
                        <label className="form-label" style={{ fontSize: '12px' }}>Fabric Material</label>
                        <input 
                          type="text" 
                          className="form-control" 
                          style={{ fontSize: '13px', padding: '6px 10px' }}
                          value={studioFabric}
                          onChange={(e) => setStudioFabric(e.target.value)}
                          placeholder="e.g. Velvet, Raw Silk, Organza"
                        />
                      </div>

                      <div className="form-group">
                        <label className="form-label" style={{ fontSize: '12px' }}>Color Palette</label>
                        <input 
                          type="text" 
                          className="form-control" 
                          style={{ fontSize: '13px', padding: '6px 10px' }}
                          value={studioColors}
                          onChange={(e) => setStudioColors(e.target.value)}
                          placeholder="e.g. Navy Blue & Gold, Rose Pink"
                        />
                      </div>

                      <div className="form-group">
                        <label className="form-label" style={{ fontSize: '12px' }}>Embroidery Style</label>
                        <input 
                          type="text" 
                          className="form-control" 
                          style={{ fontSize: '13px', padding: '6px 10px' }}
                          value={studioEmbroidery}
                          onChange={(e) => setStudioEmbroidery(e.target.value)}
                          placeholder="e.g. Zardozi, Chikankari stitches"
                        />
                      </div>

                      <button type="submit" className="btn btn-primary" style={{ width: '100%' }} disabled={generatingConcept}>
                        {generatingConcept ? 'Generating Concept Board...' : 'Generate AI Concept'}
                      </button>
                    </form>
                  </div>

                  {/* Multimodal Sketch Vision Analyzer */}
                  <div className="card-glass" style={{ background: 'rgba(28, 37, 65, 0.4)' }}>
                    <h3 style={{ fontSize: '18px', color: 'var(--color-pink-accent)', marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '8px' }}>
                      <Upload size={18} />
                      Sketch Analyzer & Feedback
                    </h3>
                    <form onSubmit={handleUploadSketch} style={{ display: 'flex', flexDirection: 'column', gap: '16px', height: '100%', justifyContent: 'space-between' }}>
                      <div className="form-group">
                        <label className="form-label" style={{ fontSize: '12px' }}>Upload Pencil Sketch (.jpg / .png)</label>
                        <input 
                          type="file" 
                          accept="image/*"
                          className="form-control" 
                          style={{ fontSize: '13px', padding: '8px' }}
                          onChange={(e) => {
                            if (e.target.files && e.target.files.length > 0) {
                              setSketchFile(e.target.files[0]);
                            }
                          }}
                          required
                        />
                      </div>

                      <button type="submit" className="btn btn-secondary" style={{ width: '100%', marginTop: 'auto' }} disabled={analyzingSketch}>
                        {analyzingSketch ? 'Analyzing Sketch with KANHA...' : 'Analyze Sketch'}
                      </button>

                      {sketchAnalysis && (
                        <div style={{
                          background: 'rgba(11, 19, 43, 0.6)',
                          border: '1px solid var(--color-border)',
                          borderRadius: '8px',
                          padding: '12px',
                          maxHeight: '160px',
                          overflowY: 'auto',
                          fontSize: '12px',
                          marginTop: '12px'
                        }}>
                          <strong style={{ color: 'var(--color-gold-primary)', display: 'block', marginBottom: '4px' }}>KANHA Recommendations:</strong>
                          <p style={{ whiteSpace: 'pre-wrap', color: 'var(--color-text-secondary)', lineHeight: '1.4' }}>{sketchAnalysis.analysis}</p>
                        </div>
                      )}
                    </form>
                  </div>

                </div>

                {/* Selected Moodboard & Items Grid */}
                {selectedMoodboard ? (
                  <div className="card-glass" style={{ minHeight: '400px' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderBottom: '1px solid var(--color-border)', paddingBottom: '12px', marginBottom: '20px' }}>
                      <div>
                        <h3 style={{ fontSize: '20px' }}>{selectedMoodboard.name}</h3>
                        <p style={{ fontSize: '12px', color: 'var(--color-text-secondary)' }}>Project Workspace: {selectedProject?.name}</p>
                      </div>
                      <span style={{ fontSize: '12px', background: 'rgba(232, 159, 181, 0.15)', color: 'var(--color-pink-accent)', padding: '4px 12px', borderRadius: '12px', fontWeight: 600 }}>
                        {selectedMoodboard.items.length} Items
                      </span>
                    </div>

                    {/* Add Reference Image Option Form (Attribution Required) */}
                    <div style={{
                      padding: '16px',
                      background: 'rgba(11, 19, 43, 0.4)',
                      border: '1px solid var(--color-border)',
                      borderRadius: '8px',
                      marginBottom: '24px'
                    }}>
                      <h4 style={{ fontSize: '14px', color: 'var(--color-gold-primary)', marginBottom: '12px' }}>Add Reference Image (Source Attribution Required)</h4>
                      <form onSubmit={handleAddReferenceItem} style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr 1fr auto', gap: '12px', alignItems: 'end' }}>
                        <div>
                          <label style={{ fontSize: '10px', color: 'var(--color-text-secondary)', display: 'block', marginBottom: '4px' }}>Image URL</label>
                          <input type="text" className="form-control" style={{ fontSize: '12px', padding: '6px' }} placeholder="https://..." value={refImgUrl} onChange={e => setRefImgUrl(e.target.value)} required />
                        </div>
                        <div>
                          <label style={{ fontSize: '10px', color: 'var(--color-text-secondary)', display: 'block', marginBottom: '4px' }}>Source Domain/Title</label>
                          <input type="text" className="form-control" style={{ fontSize: '12px', padding: '6px' }} placeholder="e.g. Wikipedia page" value={refTitle} onChange={e => setRefTitle(e.target.value)} required />
                        </div>
                        <div>
                          <label style={{ fontSize: '10px', color: 'var(--color-text-secondary)', display: 'block', marginBottom: '4px' }}>Source URL</label>
                          <input type="text" className="form-control" style={{ fontSize: '12px', padding: '6px' }} placeholder="https://attribution..." value={refUrl} onChange={e => setRefUrl(e.target.value)} required />
                        </div>
                        <div>
                          <label style={{ fontSize: '10px', color: 'var(--color-text-secondary)', display: 'block', marginBottom: '4px' }}>Caption</label>
                          <input type="text" className="form-control" style={{ fontSize: '12px', padding: '6px' }} placeholder="e.g. Dome shape" value={refCaption} onChange={e => setRefCaption(e.target.value)} />
                        </div>
                        <button type="submit" className="btn btn-secondary" style={{ padding: '8px 16px', fontSize: '12px' }}>Add Item</button>
                      </form>
                    </div>

                    {/* Moodboard Items Grid layout */}
                    {selectedMoodboard.items.length === 0 ? (
                      <div style={{ textAlign: 'center', color: 'var(--color-text-muted)', fontSize: '14px', paddingTop: '40px' }}>
                        No items added to this moodboard yet. Use the tools above to generate concepts or analyze sketches!
                      </div>
                    ) : (
                      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(220px, 1fr))', gap: '20px' }}>
                        {selectedMoodboard.items.map((item: any) => (
                          <div 
                            key={item.id}
                            style={{
                              background: 'rgba(11, 19, 43, 0.6)',
                              border: '1px solid var(--color-border)',
                              borderRadius: '8px',
                              padding: '12px',
                              display: 'flex',
                              flexDirection: 'column',
                              gap: '8px',
                              position: 'relative'
                            }}
                          >
                            <img 
                              src={item.file_url} 
                              alt={item.caption || "Moodboard item"}
                              style={{ width: '100%', height: '240px', objectFit: 'cover', borderRadius: '4px', background: '#0B132B' }} 
                            />
                            
                            {/* Watermark Label for AI generated content */}
                            {item.is_ai_generated && (
                              <div style={{
                                position: 'absolute',
                                top: '20px',
                                right: '20px',
                                background: 'rgba(201, 166, 91, 0.95)',
                                color: '#1C2541',
                                fontSize: '10px',
                                fontWeight: 800,
                                padding: '4px 8px',
                                borderRadius: '4px',
                                textTransform: 'uppercase',
                                letterSpacing: '0.05em',
                                border: '1px solid #ffffff'
                              }}>
                                AI Generated Concept
                              </div>
                            )}

                            <div>
                              <p style={{ fontSize: '13px', fontWeight: 600, color: 'var(--color-text-primary)', marginBottom: '4px' }}>
                                {item.caption || (item.is_ai_generated ? 'AI Design Board' : 'Sketch Outline')}
                              </p>
                              <span style={{ fontSize: '10px', color: 'var(--color-text-secondary)', display: 'block' }}>
                                Type: {item.item_type}
                              </span>

                              {/* Source Attribution for third-party reference images */}
                              {item.item_type === 'REFERENCE_IMAGE' && item.source_url && (
                                <div style={{ borderTop: '1px solid var(--color-border)', marginTop: '8px', paddingTop: '6px', fontSize: '11px' }}>
                                  <span style={{ color: 'var(--color-text-muted)', display: 'block', fontSize: '9px', textTransform: 'uppercase' }}>Source Attribution</span>
                                  <a href={item.source_url} target="_blank" rel="noreferrer" style={{ color: 'var(--color-gold-primary)', textDecoration: 'underline' }}>
                                    {item.source_title}
                                  </a>
                                </div>
                              )}
                            </div>
                          </div>
                        ))}
                      </div>
                    )}

                  </div>
                ) : (
                  <div className="card-glass" style={{ minHeight: '400px', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--color-text-muted)', fontSize: '14px' }}>
                    Select a workspace project and moodboard from the left pane to begin.
                  </div>
                )}

              </div>
            </div>
          </div>
        )}

        {activeTab === 'PORTFOLIO' && (
          <div style={{ display: 'flex', flexDirection: 'column', minHeight: 'calc(100vh - 120px)' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '32px' }}>
              <div>
                <h1 style={{ fontSize: '36px', color: 'var(--color-text-primary)' }}>Fashion Design Portfolio</h1>
                <p style={{ color: 'var(--color-pink-accent)', fontSize: '11px', textTransform: 'uppercase', letterSpacing: '0.2em', fontWeight: 700 }}>
                  Showcase, Curate & Export Creative Works
                </p>
              </div>

              {/* Action Compile Bar */}
              <div style={{ display: 'flex', gap: '16px', alignItems: 'center' }}>
                {user.role === 'FACULTY' && (
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <label style={{ fontSize: '12px', color: 'var(--color-text-secondary)' }}>View Student:</label>
                    <select 
                      className="form-control" 
                      style={{ fontSize: '13px', padding: '6px 12px', background: '#0B132B' }}
                      value={selectedPortfolioStudentId || 1}
                      onChange={(e) => setSelectedPortfolioStudentId(Number(e.target.value))}
                    >
                      <option value={1}>Aarav Mehta (Student 1)</option>
                      <option value={2}>Vihaan Malhotra (Student 2)</option>
                    </select>
                  </div>
                )}
                <button className="btn btn-primary" onClick={handleCompilePortfolio}>
                  Compile Portfolio PDF
                </button>
              </div>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: user.role === 'STUDENT' ? '320px 1fr' : '1fr', gap: '32px', alignItems: 'start' }}>
              {/* Left Column: Upload New Portfolio Item Form (Only for Student) */}
              {user.role === 'STUDENT' && (
                <div className="card-glass" style={{ background: 'rgba(28, 37, 65, 0.4)' }}>
                  <h3 style={{ fontSize: '16px', color: 'var(--color-gold-primary)', marginBottom: '16px', borderBottom: '1px solid var(--color-border)', paddingBottom: '8px' }}>
                    Add Portfolio Work
                  </h3>
                  <form onSubmit={handleCreatePortfolioItem} style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
                    <div className="form-group">
                      <label className="form-label" style={{ fontSize: '12px' }}>Project Title</label>
                      <input 
                        type="text" 
                        className="form-control" 
                        placeholder="e.g. Traditional Zardozi Lehenga"
                        value={portfolioTitle}
                        onChange={(e) => setPortfolioTitle(e.target.value)}
                        required
                      />
                    </div>

                    <div className="form-group">
                      <label className="form-label" style={{ fontSize: '12px' }}>Category</label>
                      <select 
                        className="form-control"
                        value={portfolioCategory}
                        onChange={(e) => setPortfolioCategory(e.target.value)}
                      >
                        <option value="ILLUSTRATION">Fashion Illustration</option>
                        <option value="GARMENT_DESIGN">Garment Design</option>
                        <option value="TEXTILES">Textile Projects</option>
                        <option value="EMBROIDERY">Embroidery & Crafts</option>
                        <option value="PHOTOGRAPHY">Photoshoot / Styling</option>
                        <option value="ASSIGNMENTS">Course Submissions</option>
                        <option value="FINAL_PROJECTS">Final Graduation Work</option>
                      </select>
                    </div>

                    <div className="form-group">
                      <label className="form-label" style={{ fontSize: '12px' }}>Project Image URL</label>
                      <input 
                        type="text" 
                        className="form-control" 
                        placeholder="/static/fashion_ai/... or https://..."
                        value={portfolioFileUrl}
                        onChange={(e) => setPortfolioFileUrl(e.target.value)}
                        required
                      />
                      <div style={{ display: 'flex', gap: '6px', marginTop: '6px' }}>
                        <button 
                          type="button" 
                          className="btn btn-secondary" 
                          style={{ padding: '2px 6px', fontSize: '10px' }}
                          onClick={() => setPortfolioFileUrl('/static/fashion_ai/concept_lehenga.jpg')}
                        >
                          Use Lehenga
                        </button>
                        <button 
                          type="button" 
                          className="btn btn-secondary" 
                          style={{ padding: '2px 6px', fontSize: '10px' }}
                          onClick={() => setPortfolioFileUrl('/static/fashion_ai/concept_anarkali.jpg')}
                        >
                          Use Anarkali
                        </button>
                      </div>
                    </div>

                    <div className="form-group">
                      <label className="form-label" style={{ fontSize: '12px' }}>Description & Design Notes</label>
                      <textarea 
                        className="form-control" 
                        style={{ height: '80px', fontSize: '13px' }}
                        placeholder="Detail materials, embroidery stitches, silhouette inspiration..."
                        value={portfolioDesc}
                        onChange={(e) => setPortfolioDesc(e.target.value)}
                      />
                    </div>

                    <button type="submit" className="btn btn-primary" style={{ width: '100%' }}>
                      Add to Showcase
                    </button>
                  </form>
                </div>
              )}

              {/* Right Column: Showcase grid with category filtering */}
              <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
                {/* Category Filtering Row */}
                <div style={{ display: 'flex', gap: '10px', flexWrap: 'wrap', borderBottom: '1px solid var(--color-border)', paddingBottom: '16px' }}>
                  {['ALL', 'ILLUSTRATION', 'GARMENT_DESIGN', 'TEXTILES', 'EMBROIDERY', 'PHOTOGRAPHY', 'ASSIGNMENTS', 'FINAL_PROJECTS'].map((cat) => (
                    <button
                      key={cat}
                      style={{
                        padding: '6px 14px',
                        borderRadius: '20px',
                        border: selectedPortfolioCategory === cat ? '1px solid var(--color-pink-accent)' : '1px solid var(--color-border)',
                        background: selectedPortfolioCategory === cat ? 'rgba(232, 159, 181, 0.15)' : 'rgba(11, 19, 43, 0.4)',
                        color: selectedPortfolioCategory === cat ? 'var(--color-pink-accent)' : 'var(--color-text-secondary)',
                        fontSize: '12px',
                        fontWeight: 600,
                        cursor: 'pointer',
                        textTransform: 'uppercase',
                        letterSpacing: '0.05em'
                      }}
                      onClick={() => setSelectedPortfolioCategory(cat)}
                    >
                      {cat.replace('_', ' ')}
                    </button>
                  ))}
                </div>

                {/* Items Grid */}
                {portfolioItems.filter(item => selectedPortfolioCategory === 'ALL' || item.category === selectedPortfolioCategory).length === 0 ? (
                  <div className="card-glass" style={{ minHeight: '300px', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--color-text-muted)', fontSize: '14px' }}>
                    No portfolio items listed under this category.
                  </div>
                ) : (
                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(240px, 1fr))', gap: '24px' }}>
                    {portfolioItems
                      .filter(item => selectedPortfolioCategory === 'ALL' || item.category === selectedPortfolioCategory)
                      .map((item) => (
                        <div 
                          key={item.id} 
                          className="card-glass" 
                          style={{ padding: '0', overflow: 'hidden', display: 'flex', flexDirection: 'column', border: '1px solid var(--color-border)' }}
                        >
                          <img 
                            src={item.file_url} 
                            alt={item.title}
                            style={{ width: '100%', height: '240px', objectFit: 'cover', background: '#0B132B' }}
                          />
                          <div style={{ padding: '16px', display: 'flex', flexDirection: 'column', gap: '8px', flex: 1 }}>
                            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start' }}>
                              <h4 style={{ fontSize: '16px', color: 'var(--color-text-primary)', margin: '0' }}>{item.title}</h4>
                              <span style={{ fontSize: '9px', background: 'rgba(201, 166, 91, 0.15)', color: 'var(--color-gold-primary)', padding: '2px 8px', borderRadius: '4px', textTransform: 'uppercase', fontWeight: 600 }}>
                                {item.category.replace('_', ' ')}
                              </span>
                            </div>
                            <p style={{ fontSize: '13px', color: 'var(--color-text-secondary)', margin: '0', flex: 1, lineHeight: '1.4' }}>
                              {item.description || 'No design notes provided.'}
                            </p>
                            {user.role === 'STUDENT' && (
                              <button 
                                className="btn btn-secondary" 
                                style={{ padding: '6px', fontSize: '11px', marginTop: '12px', width: '100%', border: '1px solid rgba(255, 107, 107, 0.2)', color: 'var(--color-error)' }}
                                onClick={() => handleDeletePortfolioItem(item.id)}
                              >
                                Delete Item
                              </button>
                            )}
                          </div>
                        </div>
                      ))}
                  </div>
                )}
              </div>
            </div>
          </div>
        )}

        {activeTab === 'CHAT' ? (
          <div style={{ display: 'flex', flexDirection: 'column', height: 'calc(100vh - 120px)' }}>
            <div style={{ marginBottom: '24px' }}>
              <h1 style={{ fontSize: '36px', color: 'var(--color-text-primary)' }}>KANHA Chat</h1>
              <p style={{ color: 'var(--color-pink-accent)', fontSize: '11px', textTransform: 'uppercase', letterSpacing: '0.2em', fontWeight: 700 }}>
                Real-time SFI Academic Exchange
              </p>
            </div>

            {chatError && (
              <div style={{ background: 'rgba(255, 107, 107, 0.15)', border: '1px solid var(--color-error)', color: 'var(--color-error)', padding: '12px', borderRadius: '6px', marginBottom: '20px', fontSize: '13px' }}>
                {chatError}
              </div>
            )}

            <div style={{ display: 'grid', gridTemplateColumns: '240px 1fr', gap: '24px', flex: 1, minHeight: '450px' }}>
              {/* Conversations Column */}
              <div className="card-glass" style={{ padding: '16px' }}>
                <h3 style={{ fontSize: '14px', textTransform: 'uppercase', color: 'var(--color-text-secondary)', letterSpacing: '0.1em', marginBottom: '16px', borderBottom: '1px solid var(--color-border)', paddingBottom: '8px' }}>
                  Tutors & Peers
                </h3>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                  {user.role === 'STUDENT' ? (
                    <div style={{ padding: '12px', background: 'rgba(201, 166, 91, 0.1)', borderLeft: '3px solid var(--color-gold-primary)', borderRadius: '6px', fontSize: '13px' }}>
                      <strong style={{ display: 'block' }}>Prof. Sarah Jenkins</strong>
                      <span style={{ fontSize: '10px', color: 'var(--color-pink-accent)', fontWeight: 700 }}>FACULTY</span>
                    </div>
                  ) : user.role === 'FACULTY' ? (
                    <>
                      <div 
                        style={{ 
                          padding: '12px', 
                          background: recipientId === 3 ? 'rgba(201, 166, 91, 0.1)' : 'rgba(11, 19, 43, 0.3)', 
                          borderLeft: recipientId === 3 ? '3px solid var(--color-gold-primary)' : '3px solid transparent', 
                          borderRadius: '6px', 
                          fontSize: '13px',
                          cursor: 'pointer'
                        }}
                        onClick={() => { if (recipientId !== 3) { setRecipientId(3); setChatMessages([]); } }}
                      >
                        <strong style={{ display: 'block' }}>Aarav Mehta</strong>
                        <span style={{ fontSize: '10px', color: 'var(--color-pink-accent)', fontWeight: 700 }}>STUDENT</span>
                      </div>
                      <div 
                        style={{ 
                          padding: '12px', 
                          background: recipientId === 4 ? 'rgba(201, 166, 91, 0.1)' : 'rgba(11, 19, 43, 0.3)', 
                          borderLeft: recipientId === 4 ? '3px solid var(--color-gold-primary)' : '3px solid transparent', 
                          borderRadius: '6px', 
                          fontSize: '13px',
                          cursor: 'pointer'
                        }}
                        onClick={() => { if (recipientId !== 4) { setRecipientId(4); setChatMessages([]); } }}
                      >
                        <strong style={{ display: 'block' }}>Diya Sharma</strong>
                        <span style={{ fontSize: '10px', color: 'var(--color-pink-accent)', fontWeight: 700 }}>STUDENT</span>
                      </div>
                    </>
                  ) : (
                    <p style={{ fontSize: '13px', color: 'var(--color-text-secondary)' }}>Chat is only available for student and faculty exchanges.</p>
                  )}
                </div>
              </div>

              {/* Chat Window Column */}
              <div className="card-glass" style={{ display: 'flex', flexDirection: 'column', padding: '20px', background: 'rgba(28, 37, 65, 0.5)' }}>
                {/* Messages scroll area */}
                <div style={{ flex: 1, overflowY: 'auto', marginBottom: '20px', display: 'flex', flexDirection: 'column', gap: '12px', paddingRight: '8px' }}>
                  {chatMessages.length === 0 ? (
                    <div style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--color-text-muted)', fontSize: '14px' }}>
                      No messages in this thread. Type below to begin exchange.
                    </div>
                  ) : (
                    chatMessages.map((m, idx) => (
                      <div key={idx} style={{
                        alignSelf: m.sender_id === user.id ? 'flex-end' : 'flex-start',
                        background: m.sender_id === user.id ? 'rgba(232, 159, 181, 0.15)' : 'rgba(11, 19, 43, 0.6)',
                        border: m.sender_id === user.id ? '1px solid rgba(232, 159, 181, 0.3)' : '1px solid var(--color-border)',
                        padding: '10px 14px',
                        borderRadius: '12px',
                        maxWidth: '70%'
                      }}>
                        <p style={{ fontSize: '14px', color: 'var(--color-text-primary)' }}>{m.content}</p>
                        <span style={{ fontSize: '8px', color: 'var(--color-text-muted)', display: 'block', marginTop: '4px', textAlign: 'right' }}>
                          {new Date(m.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                        </span>
                      </div>
                    ))
                  )}
                  {partnerTyping && (
                    <div style={{ alignSelf: 'flex-start', color: 'var(--color-pink-accent)', fontSize: '11px', fontStyle: 'italic' }}>
                      Tutor is typing...
                    </div>
                  )}
                </div>

                {/* Input form */}
                {recipientId ? (
                  <form onSubmit={handleSendChatMessage} style={{ display: 'flex', gap: '12px', borderTop: '1px solid var(--color-border)', paddingTop: '16px' }}>
                    <input 
                      type="text" 
                      className="form-control" 
                      placeholder="Type a message..."
                      value={chatInput}
                      onChange={(e) => setChatInput(e.target.value)}
                      required
                    />
                    <button 
                      type="submit" 
                      className="btn btn-primary" 
                      style={{ padding: '0 24px' }}
                      disabled={wsReadyState !== WebSocket.OPEN}
                    >
                      {wsReadyState === WebSocket.CONNECTING ? 'Connecting...' : 'Send'}
                    </button>
                  </form>
                ) : (
                  <div style={{ textAlign: 'center', color: 'var(--color-text-muted)', fontSize: '13px', borderTop: '1px solid var(--color-border)', paddingTop: '16px' }}>
                    Select a conversation target to begin chatting.
                  </div>
                )}
              </div>
            </div>
          </div>
        ) : (
          <>
            {/* --- STUDENT DASHBOARD --- */}
            {user.role === 'STUDENT' && activeTab === 'DASHBOARD' && (
          <div>
            <div style={{ marginBottom: '40px' }}>
              <p style={{ color: 'var(--color-text-secondary)', fontSize: '14px', textTransform: 'uppercase', letterSpacing: '0.1em' }}>Studio Workboard</p>
              <h1 style={{ fontSize: '48px', fontWeight: 500, color: 'var(--color-text-primary)' }}>
                Good morning, {user.first_name} 👋
              </h1>
            </div>

            {/* KANHA Assistant Banner */}
            <div className="card-glass" style={{ 
              background: 'linear-gradient(135deg, rgba(28, 37, 65, 0.9) 0%, rgba(11, 19, 43, 0.9) 100%)',
              border: '1px solid var(--color-pink-accent)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              gap: '24px',
              marginBottom: '32px'
            }}>
              <div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px' }}>
                  <Sparkles size={16} style={{ color: 'var(--color-pink-accent)' }} />
                  <span style={{ fontSize: '12px', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.1em', color: 'var(--color-pink-accent)' }}>
                    KANHA Companion Suggestion
                  </span>
                </div>
                <h3 style={{ fontSize: '20px', fontWeight: 500, marginBottom: '4px' }}>
                  "You have one assignment due tomorrow. Want to work on it together?"
                </h3>
                <p style={{ color: 'var(--color-text-secondary)', fontSize: '14px' }}>
                  I can explain design motifs or summarize search reference points for your sketches.
                </p>
              </div>
              <button className="btn btn-secondary" style={{ whiteSpace: 'nowrap' }}>
                Open Chat Assistant
              </button>
            </div>

            {/* Today's Studio Widget */}
            <h2 style={{ fontSize: '28px', marginBottom: '20px' }}>Today's Studio</h2>
            
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '24px' }}>
              
              {/* Task list card */}
              <div className="card-glass">
                <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '20px', borderBottom: '1px solid var(--color-border)', paddingBottom: '12px' }}>
                  <Clock size={20} style={{ color: 'var(--color-gold-primary)' }} />
                  <h3 style={{ fontSize: '20px' }}>Active Assignments</h3>
                </div>
                
                {assignments.length === 0 ? (
                  <p style={{ color: 'var(--color-text-secondary)', fontSize: '14px' }}>No active assignments.</p>
                ) : (
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
                    {assignments.map(a => {
                      const hasSubmission = submissions.find(s => s.assignment_id === a.id);
                      return (
                        <div key={a.id} style={{ 
                          background: 'rgba(11, 19, 43, 0.4)', 
                          padding: '16px', 
                          borderRadius: '8px',
                          borderLeft: '4px solid var(--color-gold-primary)',
                          cursor: 'pointer'
                        }} onClick={() => setSelectedAssignment(a)}>
                          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '6px' }}>
                            <h4 style={{ fontSize: '16px', fontWeight: 600 }}>{a.title}</h4>
                            {hasSubmission ? (
                              <span style={{ 
                                fontSize: '10px', 
                                background: hasSubmission.status === 'APPROVED' ? 'rgba(81, 207, 98, 0.15)' : 'rgba(232, 159, 181, 0.15)',
                                color: hasSubmission.status === 'APPROVED' ? 'var(--color-success)' : 'var(--color-pink-accent)',
                                padding: '2px 6px',
                                borderRadius: '4px',
                                textTransform: 'uppercase',
                                fontWeight: 700
                              }}>
                                {hasSubmission.status}
                              </span>
                            ) : (
                              <span style={{ fontSize: '11px', color: 'var(--color-pink-accent)', fontWeight: 700, textTransform: 'uppercase' }}>
                                {a.priority}
                              </span>
                            )}
                          </div>
                          <p style={{ color: 'var(--color-text-secondary)', fontSize: '13px', marginBottom: '12px' }}>{a.description}</p>
                          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontSize: '12px' }}>
                            <span style={{ color: 'var(--color-text-muted)' }}>Due: {new Date(a.deadline).toLocaleDateString()}</span>
                            <span style={{ color: 'var(--color-gold-primary)', fontSize: '12px', fontWeight: 600 }}>Open Details →</span>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                )}
              </div>

              {/* Class Milestones */}
              <div className="card-glass">
                <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '20px', borderBottom: '1px solid var(--color-border)', paddingBottom: '12px' }}>
                  <Calendar size={20} style={{ color: 'var(--color-pink-accent)' }} />
                  <h3 style={{ fontSize: '20px' }}>Schedule</h3>
                </div>
                
                <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
                  <div style={{ background: 'rgba(11, 19, 43, 0.4)', padding: '16px', borderRadius: '8px' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '6px' }}>
                      <h4 style={{ fontSize: '16px', fontWeight: 600 }}>Fashion Illustration critique</h4>
                      <span style={{ background: 'rgba(81, 207, 98, 0.15)', color: 'var(--color-success)', padding: '2px 8px', borderRadius: '4px', fontSize: '10px', fontWeight: 700 }}>
                        CLASS
                      </span>
                    </div>
                    <p style={{ color: 'var(--color-text-secondary)', fontSize: 13 }}>An open critique session on design illustrations.</p>
                  </div>
                </div>
              </div>

              {/* KANHA AI Doubt Solutions */}
              <div className="card-glass">
                <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '20px', borderBottom: '1px solid var(--color-border)', paddingBottom: '12px' }}>
                  <HelpCircle size={20} style={{ color: 'var(--color-pink-accent)' }} />
                  <h3 style={{ fontSize: '20px' }}>AI Doubt Solutions</h3>
                </div>

                {issues.length === 0 ? (
                  <p style={{ color: 'var(--color-text-secondary)', fontSize: '14px' }}>No active doubt tickets.</p>
                ) : (
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
                    {issues.map(i => (
                      <div key={i.id} style={{ 
                        background: 'rgba(11, 19, 43, 0.4)', 
                        padding: '16px', 
                        borderRadius: '8px',
                        borderLeft: '4px solid var(--color-pink-accent)',
                        cursor: 'pointer'
                      }} onClick={() => setSelectedIssue(i)}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '6px' }}>
                          <h4 style={{ fontSize: '15px', fontWeight: 600 }}>{i.description}</h4>
                          <span style={{ fontSize: '10px', background: 'rgba(232, 159, 181, 0.15)', color: 'var(--color-pink-accent)', padding: '2px 6px', borderRadius: '4px', textTransform: 'uppercase', fontWeight: 700 }}>
                            Level {i.escalation_level}
                          </span>
                        </div>
                        <span style={{ fontSize: '11px', color: 'var(--color-text-muted)' }}>Status: {i.status}</span>
                      </div>
                    ))}
                  </div>
                )}
              </div>

            {/* Today's Studio Progress Analytics Widgets */}
            {studentAnalytics && (
              <div style={{ marginTop: '40px', display: 'flex', flexDirection: 'column', gap: '24px' }}>
                <h3 style={{ fontSize: '22px', color: 'var(--color-gold-primary)', display: 'flex', alignItems: 'center', gap: '10px' }}>
                  <Sparkles size={20} style={{ color: 'var(--color-gold-primary)' }} />
                  Your Studio Progress & Analytics
                </h3>
                
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '24px' }}>
                  {/* Attendance Card */}
                  <div className="card-glass" style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '20px' }}>
                    <div>
                      <span style={{ fontSize: '11px', textTransform: 'uppercase', color: 'var(--color-text-secondary)', display: 'block', marginBottom: '6px' }}>Attendance Rate</span>
                      <strong style={{ fontSize: '32px', color: studentAnalytics.attendance_rate < 75 ? 'var(--color-error)' : 'var(--color-text-primary)' }}>
                        {studentAnalytics.attendance_rate}%
                      </strong>
                      <span style={{ fontSize: '11px', color: 'var(--color-text-muted)', display: 'block', marginTop: '4px' }}>
                        ({studentAnalytics.present_classes}/{studentAnalytics.total_classes} classes)
                      </span>
                    </div>
                    {/* Ring gauge representation */}
                    <div style={{
                      width: '60px', height: '60px', borderRadius: '50%',
                      background: `conic-gradient(var(--color-gold-primary) ${studentAnalytics.attendance_rate}%, rgba(11,19,43,0.4) 0)`,
                      display: 'flex', alignItems: 'center', justifyContent: 'center',
                      boxShadow: '0 0 10px rgba(0,0,0,0.2)'
                    }}>
                      <div style={{ width: '48px', height: '48px', borderRadius: '50%', background: '#1c2541', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '10px', fontWeight: 'bold' }}>
                        GAUGE
                      </div>
                    </div>
                  </div>

                  {/* Portfolio Count Card */}
                  <div className="card-glass" style={{ padding: '20px' }}>
                    <span style={{ fontSize: '11px', textTransform: 'uppercase', color: 'var(--color-text-secondary)', display: 'block', marginBottom: '6px' }}>Showcase Items</span>
                    <strong style={{ fontSize: '32px', color: 'var(--color-pink-accent)' }}>
                      {studentAnalytics.portfolio_items_count} Works
                    </strong>
                    <span style={{ fontSize: '11px', color: 'var(--color-text-muted)', display: 'block', marginTop: '4px' }}>
                      Grouped by design categories
                    </span>
                  </div>

                  {/* Submission Statistics Card */}
                  <div className="card-glass" style={{ padding: '20px' }}>
                    <span style={{ fontSize: '11px', textTransform: 'uppercase', color: 'var(--color-text-secondary)', display: 'block', marginBottom: '6px' }}>Approved Submissions</span>
                    <strong style={{ fontSize: '32px', color: 'var(--color-success)' }}>
                      {studentAnalytics.submission_stats.approved} / {
                        studentAnalytics.submission_stats.approved + 
                        studentAnalytics.submission_stats.submitted + 
                        studentAnalytics.submission_stats.revision_required + 
                        studentAnalytics.submission_stats.under_review
                      }
                    </strong>
                    <span style={{ fontSize: '11px', color: 'var(--color-text-muted)', display: 'block', marginTop: '4px' }}>
                      Approved assignments compliance
                    </span>
                  </div>
                </div>

                {/* Grade Trend Table Representation */}
                {studentAnalytics.grade_trend.length > 0 && (
                  <div className="card-glass" style={{ padding: '20px' }}>
                    <h4 style={{ fontSize: '16px', color: 'var(--color-text-primary)', marginBottom: '16px', borderBottom: '1px solid var(--color-border)', paddingBottom: '8px' }}>
                      Academic Performance & Grade Trends
                    </h4>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
                      {studentAnalytics.grade_trend.map((trend: any, idx: number) => (
                        <div key={idx} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', background: 'rgba(11, 19, 43, 0.4)', padding: '10px 16px', borderRadius: '6px' }}>
                          <span style={{ fontSize: '14px', color: 'var(--color-text-primary)' }}>{trend.assignment}</span>
                          <span style={{ 
                            fontSize: '12px', 
                            background: 'rgba(201, 166, 91, 0.15)', 
                            color: 'var(--color-gold-primary)', 
                            padding: '4px 10px', 
                            borderRadius: '12px',
                            fontWeight: 'bold'
                          }}>
                            Grade: {trend.grade} ({trend.score}%)
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}

            </div>

            {/* Student Assignment detail modal */}
            {selectedAssignment && (
              <div style={{
                position: 'fixed',
                top: 0, left: 0, right: 0, bottom: 0,
                backgroundColor: 'rgba(11, 19, 43, 0.85)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                padding: '24px',
                zIndex: 1000
              }}>
                <div className="card-glass" style={{ width: '100%', maxWidth: '640px', maxHeight: '90vh', overflowY: 'auto', border: '1px solid var(--color-gold-primary)' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '20px', borderBottom: '1px solid var(--color-border)', paddingBottom: '12px' }}>
                    <div>
                      <h3 style={{ fontSize: '24px' }}>{selectedAssignment.title}</h3>
                      <p style={{ fontSize: '13px', color: 'var(--color-text-secondary)' }}>Category: {selectedAssignment.category || 'General'}</p>
                    </div>
                    <button className="btn btn-text" onClick={() => { setSelectedAssignment(null); setSubmissionSuccess(''); setIssueSuccess(''); }} style={{ fontSize: '20px' }}>×</button>
                  </div>

                  <div style={{ marginBottom: '24px' }}>
                    <h4 style={{ fontSize: '14px', textTransform: 'uppercase', color: 'var(--color-gold-primary)', marginBottom: '8px' }}>Description</h4>
                    <p style={{ fontSize: '15px', color: 'var(--color-text-primary)' }}>{selectedAssignment.description}</p>
                  </div>

                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px', marginBottom: '32px', padding: '16px', background: 'rgba(11, 19, 43, 0.4)', borderRadius: '8px' }}>
                    <div>
                      <span style={{ fontSize: '11px', textTransform: 'uppercase', color: 'var(--color-text-secondary)', display: 'block' }}>Deadline</span>
                      <strong>{new Date(selectedAssignment.deadline).toLocaleString()}</strong>
                    </div>
                    <div>
                      <span style={{ fontSize: '11px', textTransform: 'uppercase', color: 'var(--color-text-secondary)', display: 'block' }}>Evaluation Criteria</span>
                      <strong>{selectedAssignment.grading_criteria || 'Qualitative feedback'}</strong>
                    </div>
                  </div>

                  {/* Google Workspace Attachments */}
                  {selectedAssignment.drive_file_id && (
                    <div style={{ 
                      marginBottom: '24px', 
                      padding: '16px', 
                      background: 'rgba(201, 166, 91, 0.05)', 
                      border: '1px solid var(--color-gold-primary)', 
                      borderRadius: '8px',
                      display: 'flex',
                      justifyContent: 'space-between',
                      alignItems: 'center'
                    }}>
                      <div>
                        <span style={{ fontSize: '11px', textTransform: 'uppercase', color: 'var(--color-gold-primary)', display: 'block', fontWeight: 700 }}>
                          Faculty Attachment (Google Drive)
                        </span>
                        <strong style={{ fontSize: '14px', color: 'var(--color-text-primary)' }}>{selectedAssignment.drive_file_name}</strong>
                      </div>
                      <a 
                        href={`http://localhost:8000/api/v1/google/drive/stream/${selectedAssignment.drive_file_id}`}
                        download
                        className="btn btn-secondary" 
                        style={{ fontSize: '12px', padding: '8px 16px' }}
                      >
                        Download Study Guide
                      </a>
                    </div>
                  )}

                  {/* Submission form */}
                  <div style={{ borderTop: '1px solid var(--color-border)', paddingTop: '20px' }}>
                    <h4 style={{ fontSize: '16px', marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '8px' }}>
                      <FileText size={18} style={{ color: 'var(--color-pink-accent)' }} />
                      Upload Project Submission
                    </h4>

                    {submissionSuccess && (
                      <div style={{
                        backgroundColor: submissionSuccess.includes('Error') ? 'rgba(255, 107, 107, 0.15)' : 'rgba(81, 207, 102, 0.15)',
                        border: '1px solid ' + (submissionSuccess.includes('Error') ? 'var(--color-error)' : 'var(--color-success)'),
                        color: submissionSuccess.includes('Error') ? 'var(--color-error)' : 'var(--color-success)',
                        padding: '12px',
                        borderRadius: '6px',
                        fontSize: '14px',
                        marginBottom: '20px'
                      }}>
                        {submissionSuccess}
                      </div>
                    )}

                    <form onSubmit={handleUploadSubmission}>
                      <div className="form-group">
                        <label className="form-label">Submission Description</label>
                        <textarea 
                          className="form-control" 
                          rows={3} 
                          placeholder="Describe the materials, fabrics, silhouettes, or design inspiration you used..."
                          value={submissionText}
                          onChange={(e) => setSubmissionText(e.target.value)}
                        />
                      </div>
                      <button type="submit" className="btn btn-primary" style={{ width: '100%' }}>
                        Submit Work
                      </button>
                    </form>
                  </div>

                  {/* Need Help Form */}
                  <div style={{ borderTop: '1px solid var(--color-border)', marginTop: '24px', paddingTop: '20px' }}>
                    <h4 style={{ fontSize: '16px', marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '8px' }}>
                      <HelpCircle size={18} style={{ color: 'var(--color-gold-primary)' }} />
                      Need Help? (KANHA AI Escalation Support)
                    </h4>

                    {issueSuccess && (
                      <div style={{
                        backgroundColor: 'rgba(81, 207, 102, 0.15)',
                        border: '1px solid var(--color-success)',
                        color: 'var(--color-success)',
                        padding: '12px',
                        borderRadius: '6px',
                        fontSize: '14px',
                        marginBottom: '20px'
                      }}>
                        {issueSuccess}
                      </div>
                    )}

                    <form onSubmit={handleCreateIssue}>
                      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
                        <div className="form-group">
                          <label className="form-label">Category</label>
                          <select 
                            className="form-control"
                            value={issueCategory}
                            onChange={(e) => setIssueCategory(e.target.value)}
                          >
                            <option value="INSTRUCTION_HELP">I don't understand the task</option>
                            <option value="TECHNIQUE_HELP">I need help with the technique</option>
                            <option value="EXTENSION_REQUEST">I need more time (Level 3 Escalation)</option>
                            <option value="OTHER">Other question</option>
                          </select>
                        </div>
                        <div className="form-group">
                          <label className="form-label">Describe the problem</label>
                          <input 
                            type="text" 
                            className="form-control" 
                            placeholder="What are you stuck on?"
                            value={issueDesc}
                            onChange={(e) => setIssueDesc(e.target.value)}
                            required
                          />
                        </div>
                      </div>
                      <button type="submit" className="btn btn-secondary" style={{ width: '100%' }}>
                        Ask KANHA / Request Faculty Review
                      </button>
                    </form>
                  </div>

                </div>
              </div>
            )}
          </div>
        )}

        {/* --- FACULTY DASHBOARD --- */}
        {user.role === 'FACULTY' && activeTab === 'DASHBOARD' && (
          <div>
            <div style={{ marginBottom: '40px' }}>
              <p style={{ color: 'var(--color-text-secondary)', fontSize: '14px', textTransform: 'uppercase', letterSpacing: '0.1em' }}>Faculty Hub</p>
              <h1 style={{ fontSize: '48px', fontWeight: 500, color: 'var(--color-text-primary)' }}>
                What needs attention today?
              </h1>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(360px, 1fr))', gap: '32px' }}>
              
              {/* Creator Form */}
              <div className="card-glass">
                <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '24px', borderBottom: '1px solid var(--color-border)', paddingBottom: '12px' }}>
                  <FolderPlus size={20} style={{ color: 'var(--color-gold-primary)' }} />
                  <h3 style={{ fontSize: '20px' }}>Publish Assignment</h3>
                </div>

                {assignmentSuccess && (
                  <div style={{
                    backgroundColor: assignmentSuccess.includes('Error') ? 'rgba(255, 107, 107, 0.15)' : 'rgba(81, 207, 102, 0.15)',
                    border: '1px solid ' + (assignmentSuccess.includes('Error') ? 'var(--color-error)' : 'var(--color-success)'),
                    color: assignmentSuccess.includes('Error') ? 'var(--color-error)' : 'var(--color-success)',
                    padding: '12px',
                    borderRadius: '6px',
                    fontSize: '14px',
                    marginBottom: '20px'
                  }}>
                    {assignmentSuccess}
                  </div>
                )}

                <form onSubmit={handleCreateAssignment}>
                  <div className="form-group">
                    <label className="form-label">Assignment Title</label>
                    <input 
                      type="text" 
                      className="form-control" 
                      placeholder="e.g. Surface ornamentation construction"
                      value={newTitle}
                      onChange={(e) => setNewTitle(e.target.value)}
                      required
                    />
                  </div>
                  <div className="form-group">
                    <label className="form-label">Instructions / Description</label>
                    <textarea 
                      className="form-control" 
                      rows={3} 
                      placeholder="Detailed instructions for the student task..."
                      value={newDesc}
                      onChange={(e) => setNewDesc(e.target.value)}
                      required
                      style={{ resize: 'vertical' }}
                    />
                  </div>
                  
                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
                    <div className="form-group">
                      <label className="form-label">Deadline</label>
                      <input 
                        type="datetime-local" 
                        className="form-control" 
                        value={newDeadline}
                        onChange={(e) => setNewDeadline(e.target.value)}
                        required
                      />
                    </div>
                    <div className="form-group">
                      <label className="form-label">Priority</label>
                      <select 
                        className="form-control"
                        value={newPriority}
                        onChange={(e) => setNewPriority(e.target.value)}
                      >
                        <option value="LOW">Low</option>
                        <option value="MEDIUM">Medium</option>
                        <option value="HIGH">High</option>
                      </select>
                    </div>
                  </div>

                  <div className="form-group">
                    <label className="form-label">Category</label>
                    <input 
                      type="text" 
                      className="form-control" 
                      placeholder="e.g. Textiles, Draping"
                      value={newCategory}
                      onChange={(e) => setNewCategory(e.target.value)}
                    />
                  </div>

                  <div className="form-group">
                    <label className="form-label">Grading Rubric</label>
                    <input 
                      type="text" 
                      className="form-control" 
                      placeholder="e.g. Presentation (50%), Accuracy (50%)"
                      value={newGrading}
                      onChange={(e) => setNewGrading(e.target.value)}
                    />
                  </div>

                  <div className="form-group" style={{ marginBottom: '16px' }}>
                    <label className="form-label">Study Guide (Google Drive)</label>
                    {attachedDriveFile ? (
                      <div style={{ 
                        background: 'rgba(81, 207, 102, 0.1)', 
                        border: '1px solid var(--color-success)', 
                        color: 'var(--color-success)', 
                        padding: '10px 14px', 
                        borderRadius: '6px', 
                        fontSize: '13px', 
                        display: 'flex', 
                        justifyContent: 'space-between', 
                        alignItems: 'center' 
                      }}>
                        <span>📎 {attachedDriveFile.name}</span>
                        <button type="button" className="btn btn-text" onClick={() => setAttachedDriveFile(null)} style={{ color: 'var(--color-error)', padding: 0 }}>Remove</button>
                      </div>
                    ) : (
                      <button type="button" className="btn btn-secondary" style={{ width: '100%', fontSize: '13px' }} onClick={() => setAttachedDriveFile({ id: 'drive-file-1', name: 'SFI Mughal Costume & Architecture Guidelines.pdf' })}>
                        Select File from Google Drive
                      </button>
                    )}
                  </div>

                  <button type="submit" className="btn btn-primary" style={{ width: '100%', marginTop: '16px' }}>
                    Publish to Student Portals
                  </button>
                </form>
              </div>

              {/* Submissions review checklist */}
              <div className="card-glass">
                <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '24px', borderBottom: '1px solid var(--color-border)', paddingBottom: '12px' }}>
                  <CheckCircle size={20} style={{ color: 'var(--color-pink-accent)' }} />
                  <h3 style={{ fontSize: '20px' }}>Student Submissions</h3>
                </div>

                {submissions.length === 0 ? (
                  <p style={{ color: 'var(--color-text-secondary)', fontSize: '14px' }}>No student submissions uploaded yet.</p>
                ) : (
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
                    {submissions.map(s => (
                      <div key={s.id} style={{ 
                        background: 'rgba(11, 19, 43, 0.4)', 
                        padding: '16px', 
                        borderRadius: '8px',
                        borderLeft: '4px solid var(--color-pink-accent)',
                        cursor: 'pointer'
                      }} onClick={() => setSelectedSubmission(s)}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '6px' }}>
                          <h4 style={{ fontSize: '16px', fontWeight: 600 }}>Submission #{s.id}</h4>
                          <span style={{ fontSize: '11px', color: 'var(--color-pink-accent)', fontWeight: 700, textTransform: 'uppercase' }}>
                            {s.status}
                          </span>
                        </div>
                        <p style={{ color: 'var(--color-text-secondary)', fontSize: '13px' }}>{s.submission_text}</p>
                        <p style={{ fontSize: '11px', color: 'var(--color-text-muted)', marginTop: '8px' }}>
                          Uploaded: {new Date(s.submitted_at).toLocaleString()}
                        </p>
                      </div>
                    ))}
                  </div>
                )}
              </div>

            </div>

            {/* Escalated Issues Sidebar */}
            <div className="card-glass" style={{ marginTop: '32px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '24px', borderBottom: '1px solid var(--color-border)', paddingBottom: '12px' }}>
                <AlertCircle size={20} style={{ color: 'var(--color-error)' }} />
                <h3 style={{ fontSize: '20px' }}>KANHA Escalation Support Tickets</h3>
              </div>

              {issues.length === 0 ? (
                <p style={{ color: 'var(--color-text-secondary)', fontSize: '14px' }}>No active escalated requests.</p>
              ) : (
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '20px' }}>
                  {issues.map(i => (
                    <div key={i.id} style={{ 
                      background: i.status === 'ESCALATED' ? 'rgba(255, 107, 107, 0.1)' : 'rgba(11, 19, 43, 0.4)', 
                      border: i.status === 'ESCALATED' ? '1px solid var(--color-error)' : '1px solid var(--color-border)',
                      padding: '16px', 
                      borderRadius: '8px',
                      cursor: 'pointer'
                    }} onClick={() => setSelectedIssue(i)}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '6px' }}>
                        <strong style={{ fontSize: '14px' }}>Ticket #{i.id} ({i.category})</strong>
                        <span style={{ fontSize: '10px', fontWeight: 700, color: 'var(--color-error)' }}>LEVEL {i.escalation_level}</span>
                      </div>
                      <p style={{ color: 'var(--color-text-secondary)', fontSize: '13px' }}>{i.description}</p>
                      <span style={{ fontSize: '11px', color: 'var(--color-text-muted)', display: 'block', marginTop: '8px' }}>Status: {i.status}</span>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Submission evaluation modal */}
            {selectedSubmission && (
              <div style={{
                position: 'fixed',
                top: 0, left: 0, right: 0, bottom: 0,
                backgroundColor: 'rgba(11, 19, 43, 0.85)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                padding: '24px',
                zIndex: 1000
              }}>
                <div className="card-glass" style={{ width: '100%', maxWidth: '540px', border: '1px solid var(--color-gold-primary)' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '20px', borderBottom: '1px solid var(--color-border)', paddingBottom: '12px' }}>
                    <h3 style={{ fontSize: '22px' }}>Evaluate Submission #{selectedSubmission.id}</h3>
                    <button className="btn btn-text" onClick={() => { setSelectedSubmission(null); setFeedbackSuccess(''); }} style={{ fontSize: '20px' }}>×</button>
                  </div>

                  <div style={{ marginBottom: '24px', padding: '16px', background: 'rgba(11, 19, 43, 0.4)', borderRadius: '8px' }}>
                    <span style={{ fontSize: '11px', textTransform: 'uppercase', color: 'var(--color-text-secondary)', display: 'block' }}>Student Work Notes</span>
                    <p style={{ fontSize: '14px' }}>{selectedSubmission.submission_text || "No descriptive notes added."}</p>
                    {selectedSubmission.file_url && (
                      <div style={{ marginTop: '12px' }}>
                        <span style={{ fontSize: '11px', textTransform: 'uppercase', color: 'var(--color-text-secondary)', display: 'block' }}>Attached file</span>
                        <a href={`http://localhost:8000${selectedSubmission.file_url}`} target="_blank" rel="noreferrer" style={{ color: 'var(--color-pink-accent)', fontSize: '13px', textDecoration: 'underline' }}>
                          View Submission Attachment
                        </a>
                      </div>
                    )}
                  </div>

                  {feedbackSuccess && (
                    <div style={{
                      backgroundColor: 'rgba(81, 207, 102, 0.15)',
                      border: '1px solid var(--color-success)',
                      color: 'var(--color-success)',
                      padding: '12px',
                      borderRadius: '6px',
                      fontSize: '14px',
                      marginBottom: '20px'
                    }}>
                      {feedbackSuccess}
                    </div>
                  )}

                  <form onSubmit={handlePostFeedback}>
                    <div className="form-group">
                      <label className="form-label">Qualitative Review / Comments</label>
                      <textarea 
                        className="form-control" 
                        rows={3} 
                        placeholder="Write constructive advice... (Include word 'revision' to request updates)"
                        value={feedbackText}
                        onChange={(e) => setFeedbackText(e.target.value)}
                        required
                      />
                    </div>
                    <div className="form-group">
                      <label className="form-label">Grade</label>
                      <input 
                        type="text" 
                        className="form-control" 
                        placeholder="e.g. A, B+, Pass"
                        value={feedbackGrade}
                        onChange={(e) => setFeedbackGrade(e.target.value)}
                      />
                    </div>
                    <button type="submit" className="btn btn-primary" style={{ width: '100%' }}>
                      Submit Evaluation
                    </button>
                  </form>
                </div>
              </div>
            )}

            {/* Faculty Student Watchlist Warnings System */}
            <div className="card-glass" style={{ marginTop: '32px' }}>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '24px', borderBottom: '1px solid var(--color-border)', paddingBottom: '12px' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                  <AlertTriangle size={20} style={{ color: 'var(--color-error)' }} />
                  <h3 style={{ fontSize: '20px' }}>Student Watchlist Warning System</h3>
                </div>
                <span style={{ fontSize: '11px', background: 'rgba(255,107,107,0.15)', color: 'var(--color-error)', padding: '2px 8px', borderRadius: '4px', textTransform: 'uppercase', fontWeight: 600 }}>
                  Risk watch active
                </span>
              </div>

              {facultyWarnings.length === 0 ? (
                <div style={{ background: 'rgba(81, 207, 102, 0.1)', border: '1px solid var(--color-success)', color: 'var(--color-success)', padding: '16px', borderRadius: '6px', fontSize: '14px' }}>
                  ✓ All students are fully compliant with class attendance limits (&gt;75%) and assignment submission deadlines.
                </div>
              ) : (
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '20px' }}>
                  {facultyWarnings.map((warning, idx) => (
                    <div key={idx} style={{ 
                      background: 'rgba(255, 107, 107, 0.05)', 
                      border: '1px solid rgba(255, 107, 107, 0.25)',
                      padding: '16px', 
                      borderRadius: '8px',
                      display: 'flex',
                      flexDirection: 'column',
                      gap: '8px'
                    }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                        <strong style={{ fontSize: '15px', color: 'var(--color-text-primary)' }}>{warning.name}</strong>
                        <span style={{ fontSize: '10px', background: 'rgba(255, 107, 107, 0.15)', color: 'var(--color-error)', padding: '2px 6px', borderRadius: '4px', textTransform: 'uppercase', fontWeight: 700 }}>
                          Flagged
                        </span>
                      </div>
                      <span style={{ fontSize: '12px', color: 'var(--color-text-secondary)' }}>Email: {warning.email}</span>
                      
                      <div style={{ marginTop: '6px', display: 'flex', flexDirection: 'column', gap: '4px' }}>
                        {warning.reasons.map((reason: string, rIdx: number) => (
                          <div key={rIdx} style={{ fontSize: '12px', color: 'var(--color-error)', display: 'flex', alignItems: 'center', gap: '6px' }}>
                            • {reason}
                          </div>
                        ))}
                      </div>

                      <div style={{ borderTop: '1px solid rgba(255, 107, 107, 0.15)', marginTop: '8px', paddingTop: '8px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                        <span style={{ fontSize: '11px', color: 'var(--color-text-muted)' }}>
                          Attendance: {warning.attendance_rate}%
                        </span>
                        <button 
                          className="btn btn-secondary" 
                          style={{ padding: '4px 10px', fontSize: '11px', border: '1px solid rgba(201, 166, 91, 0.4)', color: 'var(--color-gold-primary)' }}
                          onClick={() => alert(`Escalating academic intervention checklist for student ${warning.name}`)}
                        >
                          Intervene
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>

          </div>
        )}

        {/* --- ADMIN DASHBOARD --- */}
        {user.role === 'ADMIN' && (
          <div>
            <div style={{ marginBottom: '40px' }}>
              <p style={{ color: 'var(--color-text-secondary)', fontSize: '14px', textTransform: 'uppercase', letterSpacing: '0.1em' }}>Administration Portal</p>
              <h1 style={{ fontSize: '48px', fontWeight: 500, color: 'var(--color-text-primary)' }}>
                Institute Registry Control
              </h1>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(360px, 1fr))', gap: '32px' }}>
              
              {/* Register User Form */}
              <div className="card-glass">
                <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '24px', borderBottom: '1px solid var(--color-border)', paddingBottom: '12px' }}>
                  <FolderPlus size={20} style={{ color: 'var(--color-gold-primary)' }} />
                  <h3 style={{ fontSize: '20px' }}>Add User to Directory</h3>
                </div>

                {createUserSuccess && (
                  <div style={{
                    backgroundColor: createUserSuccess.includes('Error') ? 'rgba(255, 107, 107, 0.15)' : 'rgba(81, 207, 102, 0.15)',
                    border: '1px solid ' + (createUserSuccess.includes('Error') ? 'var(--color-error)' : 'var(--color-success)'),
                    color: createUserSuccess.includes('Error') ? 'var(--color-error)' : 'var(--color-success)',
                    padding: '12px',
                    borderRadius: '6px',
                    fontSize: '14px',
                    marginBottom: '20px'
                  }}>
                    {createUserSuccess}
                  </div>
                )}

                <form onSubmit={handleCreateUser}>
                  <div className="form-group">
                    <label className="form-label">Email address</label>
                    <input 
                      type="email" 
                      className="form-control" 
                      placeholder="username@kanha.local"
                      value={createEmail}
                      onChange={(e) => setCreateEmail(e.target.value)}
                      required
                    />
                  </div>
                  <div className="form-group">
                    <label className="form-label">Password</label>
                    <input 
                      type="password" 
                      className="form-control" 
                      placeholder="••••••••"
                      value={createPassword}
                      onChange={(e) => setCreatePassword(e.target.value)}
                      required
                    />
                  </div>

                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
                    <div className="form-group">
                      <label className="form-label">First Name</label>
                      <input 
                        type="text" 
                        className="form-control" 
                        placeholder="John"
                        value={createFirstName}
                        onChange={(e) => setCreateFirstName(e.target.value)}
                      />
                    </div>
                    <div className="form-group">
                      <label className="form-label">Last Name</label>
                      <input 
                        type="text" 
                        className="form-control" 
                        placeholder="Doe"
                        value={createLastName}
                        onChange={(e) => setCreateLastName(e.target.value)}
                      />
                    </div>
                  </div>

                  <div className="form-group">
                    <label className="form-label">Role</label>
                    <select 
                      className="form-control"
                      value={createRole}
                      onChange={(e) => setCreateRole(e.target.value)}
                    >
                      <option value="STUDENT">Student</option>
                      <option value="FACULTY">Faculty</option>
                      <option value="ADMIN">Administrator</option>
                    </select>
                  </div>

                  <button type="submit" className="btn btn-primary" style={{ width: '100%', marginTop: '16px' }}>
                    Register Profile
                  </button>
                </form>
              </div>

              {/* Users directory list */}
              <div className="card-glass">
                <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '24px', borderBottom: '1px solid var(--color-border)', paddingBottom: '12px' }}>
                  <Users size={20} style={{ color: 'var(--color-pink-accent)' }} />
                  <h3 style={{ fontSize: '20px' }}>Active User Directory</h3>
                </div>

                <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                  {usersList.map(u => (
                    <div key={u.id} style={{ 
                      background: 'rgba(11, 19, 43, 0.4)', 
                      padding: '12px 16px', 
                      borderRadius: '8px',
                      display: 'flex',
                      justifyContent: 'space-between',
                      alignItems: 'center'
                    }}>
                      <div>
                        <h4 style={{ fontSize: '14px', fontWeight: 600 }}>{u.first_name} {u.last_name}</h4>
                        <p style={{ color: 'var(--color-text-secondary)', fontSize: '12px' }}>{u.email}</p>
                      </div>
                      <span style={{ 
                        fontSize: '9px', 
                        fontWeight: 700, 
                        background: 'rgba(232, 159, 181, 0.15)', 
                        color: 'var(--color-pink-accent)', 
                        padding: '2px 8px', 
                        borderRadius: '4px',
                        textTransform: 'uppercase'
                      }}>
                        {u.role}
                      </span>
                    </div>
                  ))}
                </div>
              </div>

            </div>
          </div>
        )}
      </>
    )}


      {/* Issue messages thread modal */}
      {selectedIssue && (
        <div style={{
          position: 'fixed',
          top: 0, left: 0, right: 0, bottom: 0,
          backgroundColor: 'rgba(11, 19, 43, 0.85)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          padding: '24px',
          zIndex: 1000
        }}>
          <div className="card-glass" style={{ width: '100%', maxWidth: '580px', maxHeight: '80vh', display: 'flex', flexDirection: 'column', border: '1px solid var(--color-gold-primary)' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '16px', borderBottom: '1px solid var(--color-border)', paddingBottom: '12px' }}>
              <div>
                <h3 style={{ fontSize: '20px' }}>Escalation Ticket #{selectedIssue.id}</h3>
                <p style={{ fontSize: '12px', color: 'var(--color-error)' }}>Level {selectedIssue.escalation_level} Escalation ({selectedIssue.status})</p>
              </div>
              <button className="btn btn-text" onClick={() => setSelectedIssue(null)} style={{ fontSize: '20px' }}>×</button>
            </div>

            {/* Thread list */}
            <div style={{ flex: 1, overflowY: 'auto', padding: '12px 0', display: 'flex', flexDirection: 'column', gap: '12px' }}>
              {selectedIssue.messages.map(m => (
                <div key={m.id} style={{
                  alignSelf: m.sender_id === user.id ? 'flex-end' : 'flex-start',
                  background: m.sender_id === user.id 
                    ? 'rgba(232, 159, 181, 0.15)' 
                    : m.is_ai_response 
                      ? 'linear-gradient(135deg, rgba(28, 37, 65, 0.95) 0%, rgba(11, 19, 43, 0.95) 100%)' 
                      : 'rgba(11, 19, 43, 0.6)',
                  border: m.is_ai_response ? '1px solid var(--color-pink-accent)' : '1px solid transparent',
                  padding: '10px 14px',
                  borderRadius: '8px',
                  maxWidth: '80%'
                }}>
                  {m.is_ai_response && (
                    <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginBottom: '6px' }}>
                      <Sparkles size={12} style={{ color: 'var(--color-pink-accent)' }} />
                      <span style={{ fontSize: '10px', color: 'var(--color-pink-accent)', fontWeight: 700 }}>KANHA AI Tutor</span>
                    </div>
                  )}
                  <p style={{ fontSize: '13px' }}>{m.content}</p>
                  <span style={{ fontSize: '9px', color: 'var(--color-text-muted)', display: 'block', marginTop: '4px' }}>
                    {new Date(m.created_at).toLocaleTimeString()}
                  </span>
                </div>
              ))}

              {/* Student Escalate Action */}
              {user.role === 'STUDENT' && selectedIssue.escalation_level === 1 && (
                <div style={{ padding: '16px', background: 'rgba(201, 166, 91, 0.05)', border: '1px solid var(--color-border)', borderRadius: '8px', marginTop: '12px', textAlign: 'center' }}>
                  <p style={{ fontSize: '13px', color: 'var(--color-text-secondary)', marginBottom: '8px' }}>Not satisfied with KANHA's AI reply?</p>
                  <button className="btn btn-secondary" onClick={() => handleEscalateIssue(selectedIssue.id)}>
                    Escalate to Faculty Review
                  </button>
                </div>
              )}

              {/* Faculty Co-Pilot Draft suggestion */}
              {user.role === 'FACULTY' && selectedIssue.escalation_level === 2 && issueDraft && (
                <div style={{ padding: '16px', background: 'rgba(201, 166, 91, 0.08)', border: '1px solid var(--color-gold-primary)', borderRadius: '8px', marginTop: '12px' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px' }}>
                    <Sparkles size={14} style={{ color: 'var(--color-gold-primary)' }} />
                    <span style={{ fontSize: '12px', fontWeight: 700, color: 'var(--color-gold-primary)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                      AI Co-Pilot Suggested Draft
                    </span>
                  </div>
                  <textarea 
                    className="form-control" 
                    rows={3} 
                    value={issueDraft}
                    onChange={(e) => setIssueDraft(e.target.value)}
                    style={{ marginBottom: '12px', fontSize: '13px', background: 'rgba(11, 19, 43, 0.6)', color: 'var(--color-text-primary)' }}
                  />
                  <button className="btn btn-primary" style={{ width: '100%' }} onClick={handleSendDraft}>
                    Approve & Send Draft Reply
                  </button>
                </div>
              )}
            </div>

            <form onSubmit={handlePostIssueMessage} style={{ borderTop: '1px solid var(--color-border)', paddingTop: '16px', marginTop: '12px', display: 'flex', gap: '12px' }}>
              <input 
                type="text" 
                className="form-control" 
                placeholder="Type official response..."
                value={issueMessageText}
                onChange={(e) => setIssueMessageText(e.target.value)}
                required
              />
              <button type="submit" className="btn btn-primary">
                Reply
              </button>
            </form>
          </div>
        </div>
      )}

      </main>
    </div>
  );
}
