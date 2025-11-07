export const seedDispatchers = () => {

  const existing = localStorage.getItem("dispatchers");
  if (existing && existing !== "[]") {
    // Dispatchers already exist, don't overwrite
    return;
  }

  localStorage.setItem(
    "dispatchers",
    JSON.stringify([
      {
        id: "dispatcher-1",
        name: "John Doe",
        files: { 
          transcriptFiles: ["call1.txt"], 
          audioFiles: ["call1.mp3"] 
        },
        grades: {
          "call1.txt": {
            grade_percentage: 60.4,
            grader_type: "ai",
            case_entry_questions: 17,
            nature_code_questions: 10,
            questions_asked_correctly: 12,
            questions_missed: 15,
            detected_nature_code: "Falls",
            per_question: {
              CE_1: { code: "1", label: "What’s the location of the emergency?", status: "Asked Correctly" },
              CE_1a: { code: "2", label: "Was the address / location confirmed / verified", status: "Not Asked" },
              CE_2: { code: "3", label: "What's the phone number you're calling from?", status: "Asked Incorrectly" },
              CE_2a: { code: "2", label: "Was the phone number documented in the entry?", status: "Not Asked" },
              CE_3: { code: "4", label: "Okay, tell me exactly what happened.", status: "Not As Scripted" },
              CE_3a: { code: "1", label: "Are you with the patient now?", status: "Asked Correctly" },
              CE_3b: { code: "2", label: "How many people are hurt/sick?", status: "Not Asked" },
              CE_4: { code: "1", label: "How old is the patient?", status: "Asked Correctly" },
              CE_5: { code: "1", label: "Is s/he awake?", status: "Asked Correctly" },
              CE_6: { code: "6", label: "Is s/he breathing?", status: "Obvious" },
              CE_7: { code: "1", label: "Awake and breathing asks separately?", status: "Asked Correctly" },
              CE_8: { code: "1", label: "Were all questions asked in order?", status: "Asked Correctly" },
              NC_1: { code: "4", label: "How far did s/he fall?", status: "Not As Scripted" },
              NC_2: { code: "4", label: "What caused the fall?", status: "Not As Scripted" },
              NC_3: { code: "2", label: "Is there any SERIOUS bleeding?", status: "Not Asked" },
              NC_4: { code: "4", label: "Is s/he completely alert?", status: "Not As Scripted" },
              NC_5: { code: "1", label: "What part of the body was injured?", status: "Asked Correctly" },
              NC_5a: { code: "2", label: "Is s/he having any difficulty breathing?", status: "Not Asked" },
              NC_5b: { code: "6", label: "Is it obviously bent out of shape?", status: "Obvious" },
              NC_6: { code: "4", label: "When did this happen?", status: "Not As Scripted" },
              NC_7: { code: "1", label: "Is s/he still on the floor/ground?", status: "Asked Correctly" },
              NC_8: { code: "1", label: "Were all key questions asked in order?", status: "Asked Correctly" }
            }
          }
        }
      }
    ])
  );
  console.log("Mock dispatcher seeded in localStorage ✅");
};
