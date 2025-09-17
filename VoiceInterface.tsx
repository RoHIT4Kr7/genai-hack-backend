import React, { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Mic, MicOff, Volume2, VolumeX, Square } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';

interface VoiceInterfaceProps {
  contactName: string;
  contactAvatar?: string;
  contactDescription?: string;
  onVoiceStart?: () => void;
  onVoiceStop?: () => void;
  onVoiceMessage?: (message: string) => void;
}

const VoiceInterface: React.FC<VoiceInterfaceProps> = ({
  contactName,
  contactAvatar,
  contactDescription,
  onVoiceStart,
  onVoiceStop,
  onVoiceMessage
}) => {
  const [isRecording, setIsRecording] = useState(false);
  const [isPlaying, setIsPlaying] = useState(false);
  const [transcript, setTranscript] = useState<string[]>([]);
  const [audioLevel, setAudioLevel] = useState(0);
  const [sessionTime, setSessionTime] = useState(0);
  
  const sessionIntervalRef = useRef<NodeJS.Timeout | null>(null);

  // Simulate audio level animation when recording
  useEffect(() => {
    let interval: NodeJS.Timeout | null = null;
    if (isRecording) {
      interval = setInterval(() => {
        setAudioLevel(Math.random() * 100);
      }, 100);
    } else {
      setAudioLevel(0);
    }
    return () => {
      if (interval) clearInterval(interval);
    };
  }, [isRecording]);

  // Session timer
  useEffect(() => {
    if (isRecording || isPlaying) {
      sessionIntervalRef.current = setInterval(() => {
        setSessionTime(prev => prev + 1);
      }, 1000);
    } else {
      if (sessionIntervalRef.current) {
        clearInterval(sessionIntervalRef.current);
      }
    }

    return () => {
      if (sessionIntervalRef.current) {
        clearInterval(sessionIntervalRef.current);
      }
    };
  }, [isRecording, isPlaying]);

  const handleToggleRecording = () => {
    if (isRecording) {
      setIsRecording(false);
      onVoiceStop?.();
      // Simulate adding a transcript
      const messages = [
        "I've been feeling a bit overwhelmed lately...",
        "Thank you for listening, I appreciate your support.",
        "Can you help me with some breathing exercises?",
        "I feel much better after talking with you."
      ];
      const randomMessage = messages[Math.floor(Math.random() * messages.length)];
      setTranscript(prev => [...prev, `You: ${randomMessage}`]);
      
      // Simulate AI response
      setTimeout(() => {
        const aiResponses = [
          `${contactName}: I understand how you're feeling. Let's work through this together.`,
          `${contactName}: That's completely normal. Would you like to try a mindfulness exercise?`,
          `${contactName}: I'm here for you. Let's focus on some positive affirmations.`,
          `${contactName}: You're doing great by reaching out. How can I support you today?`
        ];
        const randomResponse = aiResponses[Math.floor(Math.random() * aiResponses.length)];
        setTranscript(prev => [...prev, randomResponse]);
        setIsPlaying(true);
        setTimeout(() => setIsPlaying(false), 3000);
      }, 1500);
      
    } else {
      setIsRecording(true);
      onVoiceStart?.();
    }
  };

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };

  const clearSession = () => {
    setTranscript([]);
    setSessionTime(0);
    setIsRecording(false);
    setIsPlaying(false);
  };

  return (
    <div className="h-full bg-gradient-to-br from-background via-background-soft to-background flex flex-col">
      {/* Header */}
      <div className="p-6 bg-white/95 backdrop-blur-lg border-b border-border">
        <div className="flex items-center space-x-4">
          <div className="w-12 h-12 bg-gradient-to-br from-primary to-primary-dark rounded-xl flex items-center justify-center shadow-md">
            <span className="text-white text-xl">{contactName.charAt(0)}</span>
          </div>
          <div>
            <h3 className="poppins-semibold text-xl text-foreground">{contactName}</h3>
            <p className="inter-regular text-muted-foreground">{contactDescription}</p>
            {sessionTime > 0 && (
              <p className="inter-regular text-sm text-primary">Session: {formatTime(sessionTime)}</p>
            )}
          </div>
        </div>
      </div>

      {/* Main Voice Interface */}
      <div className="flex-1 flex flex-col items-center justify-center p-8">
        
        {/* Voice Visualization */}
        <div className="mb-8">
          <motion.div
            className="relative w-48 h-48 rounded-full bg-gradient-to-br from-primary/20 to-primary-dark/20 border-2 border-primary/30 flex items-center justify-center"
            animate={{ 
              scale: isRecording ? [1, 1.1, 1] : 1,
              boxShadow: isRecording 
                ? `0 0 ${20 + audioLevel}px hsl(var(--primary) / 0.3)`
                : '0 4px 20px hsl(var(--primary) / 0.1)'
            }}
            transition={{ 
              scale: { repeat: isRecording ? Infinity : 0, duration: 1 },
              boxShadow: { duration: 0.1 }
            }}
          >
            {/* Animated Waves */}
            <AnimatePresence>
              {isRecording && (
                <>
                  {[...Array(5)].map((_, i) => (
                    <motion.div
                      key={i}
                      className="absolute w-full h-full rounded-full border-2 border-primary/20"
                      initial={{ scale: 0, opacity: 1 }}
                      animate={{
                        scale: [0, 1.5, 2],
                        opacity: [1, 0.5, 0]
                      }}
                      transition={{
                        duration: 2,
                        repeat: Infinity,
                        delay: i * 0.4
                      }}
                    />
                  ))}
                </>
              )}
            </AnimatePresence>

            {/* Center Content */}
            <div className="text-6xl text-primary">
              {isRecording ? <Mic /> : isPlaying ? <Volume2 /> : <MicOff />}
            </div>
          </motion.div>
        </div>

        {/* Status Text */}
        <div className="text-center mb-8">
          <h2 className="poppins-medium text-2xl text-foreground mb-2">
            {isRecording ? 'Listening...' : isPlaying ? 'Speaking...' : 'Ready to chat'}
          </h2>
          <p className="inter-regular text-muted-foreground">
            {isRecording 
              ? 'Speak naturally, I\'m here to listen' 
              : isPlaying 
                ? 'AI is responding...'
                : 'Tap the microphone to start talking'
            }
          </p>
        </div>

        {/* Controls */}
        <div className="flex items-center space-x-6">
          <Button
            onClick={handleToggleRecording}
            className={`w-20 h-20 rounded-full ${
              isRecording 
                ? 'bg-destructive hover:bg-destructive/90' 
                : 'bg-primary hover:bg-primary-dark'
            } text-white shadow-lg hover:shadow-xl transition-all duration-300`}
            disabled={isPlaying}
          >
            {isRecording ? <Square className="h-8 w-8" /> : <Mic className="h-8 w-8" />}
          </Button>
          
          {transcript.length > 0 && (
            <Button
              onClick={clearSession}
              variant="outline"
              className="px-6 py-3 inter-medium"
            >
              Clear Session
            </Button>
          )}
        </div>
      </div>

      {/* Transcript */}
      {transcript.length > 0 && (
        <div className="p-6 bg-white/95 backdrop-blur-lg border-t border-border max-h-60 overflow-y-auto">
          <h4 className="poppins-medium text-lg text-foreground mb-4">Conversation</h4>
          <div className="space-y-3">
            {transcript.map((message, index) => (
              <motion.div
                key={index}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.3 }}
                className={`p-3 rounded-lg ${
                  message.startsWith('You:') 
                    ? 'bg-primary/10 text-foreground ml-8' 
                    : 'bg-muted text-foreground mr-8'
                }`}
              >
                <p className="inter-regular text-sm leading-relaxed">{message}</p>
              </motion.div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default VoiceInterface;