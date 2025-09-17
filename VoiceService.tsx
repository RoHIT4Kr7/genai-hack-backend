import React, { useState } from "react";
import { motion } from "framer-motion";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import LightServiceNavigation from "@/components/navigation/LightServiceNavigation";
import VoiceInterface from "@/components/voice/VoiceInterface";

interface VoiceOption {
  id: string;
  title: string;
  description: string;
  icon: string;
  personality: string;
  gradient: string;
}

const VoiceService: React.FC = () => {
  const [selectedOption, setSelectedOption] = useState<string | null>(null);

  const voiceOptions: VoiceOption[] = [
    {
      id: "friend",
      title: "Talk to Friend",
      description:
        "Chat with a supportive AI friend who listens and understands",
      icon: "👥",
      personality: "Friendly, casual, supportive, and understanding",
      gradient: "from-blue-500/20 to-cyan-500/20",
    },
    {
      id: "therapist",
      title: "Talk to Therapist",
      description:
        "Professional AI therapist for mental health support and guidance",
      icon: "🧠",
      personality:
        "Professional, empathetic, trained in therapeutic techniques",
      gradient: "from-green-500/20 to-teal-500/20",
    },
    {
      id: "teacher",
      title: "Talk to Teacher",
      description:
        "Educational AI that helps you learn and grow intellectually",
      icon: "🎓",
      personality: "Knowledgeable, patient, encouraging, and educational",
      gradient: "from-purple-500/20 to-indigo-500/20",
    },
  ];

  const handleSelectOption = (optionId: string) => {
    setSelectedOption(optionId);
  };

  const handleBackToOptions = () => {
    setSelectedOption(null);
  };

  const getContactInfo = (optionId: string) => {
    switch (optionId) {
      case "friend":
        return {
          name: "Alex - Your AI Friend",
          avatar: "/images/friend-avatar.png",
          status: "Ready to chat and listen",
        };
      case "therapist":
        return {
          name: "Dr. Sarah - AI Therapist",
          avatar: "/images/therapist-avatar.png",
          status: "Professional support available",
        };
      case "teacher":
        return {
          name: "Prof. Morgan - AI Educator",
          avatar: "/images/teacher-avatar.png",
          status: "Ready to help you learn",
        };
      default:
        return {
          name: "AI Assistant",
          avatar: "/images/default-avatar.png",
          status: "Online",
        };
    }
  };

  if (selectedOption) {
    const contactInfo = getContactInfo(selectedOption);

    return (
      <div className="min-h-screen bg-gradient-to-br from-background via-background-soft to-background flex">
        <LightServiceNavigation />

        <div className="flex-1 ml-0 lg:ml-64">
          <motion.div
            initial={{ opacity: 0, x: 100 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -100 }}
            transition={{ duration: 0.4 }}
            className="h-screen flex flex-col"
          >
            {/* Back Button */}
            <div className="p-6 bg-white/95 backdrop-blur-lg border-b border-border">
              <Button
                variant="ghost"
                onClick={handleBackToOptions}
                className="inter-medium text-foreground hover:text-primary hover:bg-primary/10 rounded-xl"
              >
                ← Back to Options
              </Button>
            </div>

            {/* Voice Interface */}
            <div className="flex-1">
              <VoiceInterface
                contactName={contactInfo.name.split(" - ")[0]}
                contactDescription={contactInfo.status}
                onVoiceStart={() => {
                  console.log(`Voice session started with ${selectedOption}`);
                }}
                onVoiceStop={() => {
                  console.log(`Voice session stopped with ${selectedOption}`);
                }}
                onVoiceMessage={(message) => {
                  console.log(`Voice message to ${selectedOption}:`, message);
                }}
              />
            </div>
          </motion.div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-background via-background-soft to-background flex">
      <LightServiceNavigation />

      <main className="flex-1 ml-0 lg:ml-64 px-4 py-8">
        <div className="max-w-6xl mx-auto py-8">
          {/* Header */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
            className="text-center mb-12"
          >
            <h1 className="text-5xl md:text-6xl lg:text-7xl poppins-bold mb-6 bg-gradient-to-r from-primary via-accent to-primary bg-clip-text text-transparent">
              Voice Chat Service
            </h1>
            <p className="text-muted-foreground text-xl md:text-2xl max-w-4xl mx-auto inter-regular leading-relaxed">
              Choose who you'd like to talk with. Each AI companion has been
              trained with different personalities and expertise to support you.
            </p>
          </motion.div>

          {/* Voice Options */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {voiceOptions.map((option, index) => (
              <motion.div
                key={option.id}
                initial={{ opacity: 0, y: 30 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.6, delay: index * 0.1 }}
                whileHover={{ y: -8 }}
                whileTap={{ scale: 0.98 }}
              >
                <Card className="service-card cursor-pointer bg-white/95 backdrop-blur-sm border border-border/50 hover:border-primary/50 hover:shadow-lg h-full transition-all duration-300">
                  <CardContent className="p-8 h-full flex flex-col">
                    <div className="flex items-center space-x-4 mb-6">
                      <div className="text-6xl">{option.icon}</div>
                      <h3 className="text-2xl poppins-semibold text-foreground">
                        {option.title}
                      </h3>
                    </div>

                    <p className="text-muted-foreground mb-6 flex-grow text-lg inter-regular leading-relaxed">
                      {option.description}
                    </p>

                    <div className="mb-8 p-4 bg-background/50 rounded-xl border border-border/30">
                      <p className="text-base text-muted-foreground inter-regular">
                        <strong className="text-foreground inter-medium">
                          Personality:
                        </strong>{" "}
                        {option.personality}
                      </p>
                    </div>

                    <Button
                      onClick={() => handleSelectOption(option.id)}
                      className="w-full bg-gradient-to-r from-primary to-primary-medium hover:from-primary-medium hover:to-primary text-primary-foreground inter-medium font-semibold py-4 text-lg rounded-2xl transition-all duration-300 shadow-md hover:shadow-lg"
                    >
                      Start Voice Chat
                    </Button>
                  </CardContent>
                </Card>
              </motion.div>
            ))}
          </div>

          {/* Features Info */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.4 }}
            className="mt-12 p-6 bg-white/95 rounded-2xl border border-border/30 backdrop-blur-sm shadow-lg"
          >
            <h3 className="text-2xl md:text-3xl poppins-semibold text-foreground mb-8 text-center">
              Voice Chat Features
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6 text-center">
              <div className="space-y-4">
                <div className="text-4xl">🎙️</div>
                <p className="text-base inter-regular text-muted-foreground">
                  Real-time voice conversations
                </p>
              </div>
              <div className="space-y-4">
                <div className="text-4xl">🧠</div>
                <p className="text-base inter-regular text-muted-foreground">
                  AI trained for emotional support
                </p>
              </div>
              <div className="space-y-4">
                <div className="text-4xl">🔒</div>
                <p className="text-base inter-regular text-muted-foreground">
                  Private and secure conversations
                </p>
              </div>
            </div>
          </motion.div>
        </div>
      </main>
    </div>
  );
};

export default VoiceService;
