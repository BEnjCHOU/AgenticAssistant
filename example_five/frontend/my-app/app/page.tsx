'use client';

import React, { useState, useEffect, useRef } from 'react';
import { Send, Upload, FileText, Bot, User, Trash2 } from 'lucide-react';
import axios, { AxiosError } from 'axios';

// --- Types ---
interface Message {
  role: 'user' | 'agent';
  content: string;
}

export default function ChatAgent() {
  const [messages, setMessages] = useState<Message[]>([
    { role: 'agent', content: 'Hello! I am your AI assistant. Upload a file or ask me anything.' }
  ]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [files, setFiles] = useState<string[]>([]);
  const [isUploading, setIsUploading] = useState(false);
  const [isUpdating, setIsUpdating] = useState(false);
  const [updatingFileName, setUpdatingFileName] = useState<string | null>(null);
  const [isDeleting, setIsDeleting] = useState(false);
  
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);        // for new uploads
  const updateFileInputRef = useRef<HTMLInputElement>(null);  // for updates

  // Backend URL
  const API_URL = 'http://localhost:8000';

  // --- Effects ---
  useEffect(() => {
    fetchFiles();
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  // --- API Calls ---
  const fetchFiles = async () => {
    try {
      const res = await axios.get(`${API_URL}/files/`);
      setFiles(res.data.files || []);
    } catch (err) {
      console.error("Error fetching files:", err);
    }
  };

  const handleSendMessage = async (e?: React.FormEvent) => {
    e?.preventDefault();
    if (!input.trim() || isLoading) return;

    const userMessage = input;
    setInput('');
    setMessages(prev => [...prev, { role: 'user', content: userMessage }]);
    setIsLoading(true);

    try {
      const res = await axios.post(`${API_URL}/ask/`, { message: userMessage });
      const agentResponse = res.data.response || "No response received.";
      setMessages(prev => [...prev, { role: 'agent', content: agentResponse }]);
    } catch (error) {
      setMessages(prev => [...prev, { role: 'agent', content: "Error: Could not connect to the agent." }]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    
    setIsUploading(true);
    const formData = new FormData();
    formData.append("file", file);

    try {
      const res = await axios.post(`${API_URL}/upload/`, formData);
      // if file exists, alert user to use update instead
      if ('error' in res.data) {
        setMessages(prev => [...prev, { 
          role: 'agent', 
          content: `${res.data.error}`
        }]);
        return
      }
      await fetchFiles();
      setMessages(prev => [...prev, { 
        role: 'agent', 
        content: `✅ Successfully processed file: ${file.name}. You can now ask questions about it.` 
      }]);
    } catch (error) {
      if (axios.isAxiosError(error) && error.response) {
        console.error("Upload failed. Server response data:", error.response.data);
        alert(`Error uploading file: ${error.response.data.message || 'Server rejected the file.'}`);
      } else {
        console.error("An unknown error occurred during upload:", error);
        alert("An unknown error occurred during file upload.");
      }
    } finally {
      setIsUploading(false);
      if (fileInputRef.current) fileInputRef.current.value = '';
    }
  };

  // --- Update feature handlers ---
  const startUpdate = (filename: string) => {
    // mark which file will be updated, then open the hidden file input
    setUpdatingFileName(filename);
    updateFileInputRef.current?.click();
  };

  const handleUpdateFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file || !updatingFileName) {
      setUpdatingFileName(null);
      if (updateFileInputRef.current) updateFileInputRef.current.value = '';
      return;
    }

    setIsUpdating(true);
    const formData = new FormData();
    formData.append("file", file);
    // include the target filename so backend knows which file to replace
    formData.append("target_filename", updatingFileName);

    try {
      const res = await axios.put(`${API_URL}/update/`, formData);
      if ('error' in res.data) {
        setMessages(prev => [...prev, { 
          role: 'agent', 
          content: `${res.data.status}\n${res.data.error}`
        }]);
        return;
      }
      console.log(res.data);
      await fetchFiles();
      setMessages(prev => [...prev, { 
        role: 'agent', 
        content: `🔁 Successfully updated ${updatingFileName} with ${file.name}.` 
      }]);
    } catch (error) {
      if (axios.isAxiosError(error) && error.response) {
        console.error("Update failed. Server response data:", error.response.data);
        alert(`Error updating file: ${error.response.data.message || 'Server rejected the file.'}`);
      } else {
        console.error("An unknown error occurred during update:", error);
        alert("An unknown error occurred during file update.");
      }
      setMessages(prev => [...prev, { role: 'agent', content: `❌ Failed to update ${updatingFileName}.` }]);
    } finally {
      setIsUpdating(false);
      setUpdatingFileName(null);
      if (updateFileInputRef.current) updateFileInputRef.current.value = '';
    }
  };

  // --- Delete feature handler ---
  const handleDeleteFile = async (filename: string) => {
    // Confirm before deleting
    if (!window.confirm(`Are you sure you want to delete ${filename}?`)) {
      return;
    }

    setIsDeleting(true);
    try {
      const res = await axios.delete(`${API_URL}/delete/${filename}`);
      if ('error' in res.data) {
        setMessages(prev => [...prev, { 
          role: 'agent', 
          content: `❌ Failed to delete ${filename}: ${res.data.error}`
        }]);
        return;
      }

      await fetchFiles();
      setMessages(prev => [...prev, { 
        role: 'agent', 
        content: `🗑️ Successfully deleted ${filename} from the knowledge base.` 
      }]);
    } catch (error) {
      if (axios.isAxiosError(error) && error.response) {
        console.error("Delete failed. Server response data:", error.response.data);
        alert(`Error deleting file: ${error.response.data.message || 'Server rejected the request.'}`);
      } else {
        console.error("An unknown error occurred during delete:", error);
        alert("An unknown error occurred during file deletion.");
      }
      setMessages(prev => [...prev, { role: 'agent', content: `❌ Failed to delete ${filename}.` }]);
    } finally {
      setIsDeleting(false);
    }
  };

  return (
    <div className="flex h-screen bg-gray-50 text-gray-900 font-sans">
      
      {/* --- Sidebar (Files) --- */}
      <div className="w-64 bg-white border-r border-gray-200 flex flex-col hidden md:flex">
        <div className="p-4 border-b border-gray-200">
          <h2 className="text-lg font-bold flex items-center gap-2 text-indigo-600">
            <Bot size={24} />
            Agent Brain
          </h2>
        </div>
        
        <div className="flex-1 overflow-y-auto p-4">
          <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-3">
            Knowledge Base
          </h3>
          <div className="space-y-2">
            {files.length === 0 ? (
              <p className="text-sm text-gray-400 italic">No files indexed yet.</p>
            ) : (
              files.map((file, idx) => (
                <div key={idx} className="flex items-center gap-2 text-sm text-gray-700 bg-gray-50 p-2 rounded-md border border-gray-100">
                  <FileText size={16} className="text-blue-500" />
                  <span className="truncate flex-1">{file}</span>

                  {/* Update button */}
                  <button
                    onClick={() => startUpdate(file)}
                    disabled={isUpdating || isUploading || isDeleting}
                    title={`Update ${file}`}
                    className="ml-1 text-xs px-2 py-1 rounded-md bg-yellow-100 text-yellow-800 hover:bg-yellow-200 transition-colors disabled:opacity-50"
                  >
                    Update
                  </button>

                  {/* Delete button */}
                  <button
                    onClick={() => handleDeleteFile(file)}
                    disabled={isDeleting || isUploading || isUpdating}
                    title={`Delete ${file}`}
                    className="ml-1 text-xs px-2 py-1 rounded-md bg-red-100 text-red-800 hover:bg-red-200 transition-colors disabled:opacity-50"
                  >
                    <Trash2 size={14} />
                  </button>
                </div>
              ))
            )}
          </div>
        </div>

        <div className="p-4 border-t border-gray-200">
          {/* hidden file inputs */}
          <input 
            type="file" 
            ref={fileInputRef}
            onChange={handleFileUpload}
            className="hidden"
          />
          <input
            type="file"
            ref={updateFileInputRef}
            onChange={handleUpdateFileChange}
            className="hidden"
          />

          <button 
            onClick={() => fileInputRef.current?.click()}
            disabled={isUploading || isUpdating || isDeleting}
            className={`w-full flex items-center justify-center gap-2 py-2 px-4 rounded-md text-white transition-colors ${
              isUploading ? 'bg-indigo-300 cursor-not-allowed' : 'bg-indigo-600 hover:bg-indigo-700'
            }`}
          >
            {isUploading ? (
              <span className="animate-pulse">Uploading...</span>
            ) : (
              <>
                <Upload size={18} />
                Upload Context
              </>
            )}
          </button>
        </div>
      </div>

      {/* --- Main Chat Area --- */}
      <div className="flex-1 flex flex-col">
        {/* Header (Mobile only) */}
        <div className="md:hidden p-4 bg-white border-b flex justify-between items-center">
          <span className="font-bold text-indigo-600">Agent Chat</span>
          <button 
             onClick={() => fileInputRef.current?.click()}
             className="text-sm text-indigo-600 font-medium"
          >
            + Upload
          </button>
        </div>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto p-4 space-y-6">
          {messages.map((msg, index) => (
            <div 
              key={index} 
              className={`flex items-start gap-4 ${msg.role === 'user' ? 'flex-row-reverse' : ''}`}
            >
              <div className={`w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 ${
                msg.role === 'user' ? 'bg-gray-800 text-white' : 'bg-indigo-100 text-indigo-600'
              }`}>
                {msg.role === 'user' ? <User size={16} /> : <Bot size={16} />}
              </div>
              
              <div className={`max-w-[80%] rounded-2xl px-4 py-3 shadow-sm ${
                msg.role === 'user' 
                  ? 'bg-blue-600 text-white rounded-tr-none' 
                  : 'bg-white border border-gray-100 text-gray-800 rounded-tl-none'
              }`}>
                 <p className="whitespace-pre-wrap leading-relaxed text-sm">
                   {msg.content}
                 </p>
              </div>
            </div>
          ))}
          
          {isLoading && (
            <div className="flex items-center gap-2 text-gray-400 text-sm ml-12">
              <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" />
              <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce [animation-delay:-0.15s]" />
              <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce [animation-delay:-0.3s]" />
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* Input Area */}
        <div className="p-4 bg-white border-t border-gray-200">
          <form onSubmit={handleSendMessage} className="max-w-4xl mx-auto relative flex gap-2">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Ask a question about your files..."
              className="flex-1 bg-gray-100 border-0 focus:ring-2 focus:ring-indigo-500 rounded-xl px-4 py-3 text-gray-800 placeholder-gray-400 outline-none transition-all"
            />
            <button 
              type="submit"
              disabled={!input.trim() || isLoading}
              className="bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed text-white p-3 rounded-xl transition-colors"
            >
              <Send size={20} />
            </button>
          </form>
          <div className="text-center mt-2">
             <p className="text-xs text-gray-400">Agent remembers context within this session.</p>
          </div>
        </div>
      </div>
    </div>
  );
}