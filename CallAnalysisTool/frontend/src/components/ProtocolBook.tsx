"use client";
import React, { useState } from "react";

const PRIMARY_NAVY = "#002d62";
const ROUNDING_CLASS = "rounded-[10px]";

//Protocol Data Array (Protocols and Questions) 
const protocols = [
  {
    id: "0",
    title: "Case Entry",
    description:
      "Gather basic information about the call, confirm details, and ensure proper documentation.",
    steps: [
      "What’s the location of the emergency?",
      "Was the address / location confirmed / verified",
      "Was the 911 CAD Dump used to build the call?",
      "What's the phone number you're calling from?",
      "Was the phone number documented in the entry?",
      "Okay, tell me exactly what happened.",
      "Fast Track Used?",
      "Are you with the patient now?",
      "How many people are hurt/sick?",
      "Is s/he breathing or coughing at all?",
      "How old is the patient?",
      "Tell me approximately, then.",
      "Is s/he awake?",
      "Is s/he breathing?",
      "You go check and tell me what you find.",
      "Awake and breathing asks separately?",
      "Were all questions asked in order?",
    ],
  },
  {
    id: "1",
    title: "Abdominal Pain / Problems",
    description: "Assess abdominal pain and associated symptoms to determine urgency.",
    steps: [
      "Is s/he completely alert?",
      "Has s/he ever been diagnosed w/ aortic aneurysm?",
      "Ask her/him to describe the pain",
      "Did s/he faint or nearly faint?",
      "Is her/his pain above the belly button?",
      "Were all key questions asked in order?",
    ],
  },
  {
    id: "2",
    title: "Allergies / Envenomations",
    description:
      "Identify severity of reaction and ensure airway is not compromised.",
    steps: [
      "Where is the snake now?",
      "Is s/he completely alert?",
      "Does s/he have difficulty breathing or swallowing?",
      "Does s/he have difficulty speaking?",
      "Has s/he ever had a severe allergic reaction before?",
      "Does s/he have any specific injections or meds for this?",
      "Have they been used?",
      "Tell him/her to use them now?",
      "Were all key questions asked in order?",
    ],
  },
  {
    id: "3",
    title: "Animal Bites/ Attacks",
    description: "Determine the type and severity of the bite and risk of infection.",
    steps: [
      "What kind of animal is it?",
      "Where is the animal now?",
      "Is there any SERIOUS bleeding?",
      "Is s/he completely alert?",
      "What part of the body was injured/bitten?",
      "Is s/he having any difficulty breathing?",
      "What kind of injuries does s/he have?",
      "When did this happen?",
      "Were all key questions asked in order?",
    ],
  },
  {
    id: "4",
    title: "Assault / Sexual Assault / Stun Gun",
    description: "Ensure patient safety and gather necessary details for emergency response.",
    steps: [
      "Is the assailant still nearby?",
      "Were weapons involved or mentioned?",
      "Is there any SERIOUS bleeding?",
      "Is s/he completely alert?",
      "What part of the body was injured?",
      "Does s/he have any other injuries?",
      "Is s/he having any difficulty breathing?",
      "Is it obviously bent out of shape?",
      "When did this happen?",
      "Were all key questions asked in order?",
    ],
  },
  {
    id: "5",
    title: "Back Pain (Non-Traumatic or Non-Recent Trauma)",
    description:
      "Assess pain characteristics and associated symptoms to determine urgency.",
    steps: [
      "When did this start?",
      "What caused the back pain?",
      "Does s/he have difficulty breathing?",
      "Does s/he also have chest pain or chest discomfort?",
      "Is s/he completely alert?",
      "Has s/he ever been diagnosed with an aortic aneurysm?",
      "Ask her/him to describe the pain",
      "Did s/he faint or nearly faint?",
      "Were all key questions asked in order?",
    ],
  },
  {
    id: "6",
    title: "Breathing Problems",
    description:
      "Assess patient's breathing status and history of respiratory issues.",
    steps: [
      "Is s/he completely alert?",
      "Does s/he any difficulty speaking/crying between breaths?",
      "Is s/he changing color?",
      "Describe the color change?",
      "Is s/he clammy or having cold sweats?",
      "Does s/he have asthma or other lung problems?",
      "Does s/he have a prescribed inhaler?",
      "Has s/he used it yet?",
      "Does s/he have any special equipment or instructions?",
      "Have they been used?",
      "Were all key questions asked in order?",
    ],
  },
  {
    id: "7",
    title: "Burns (Scalds) / Explosion (Blast)",
    description:
      "Determine the cause and extent of burns/injuries and check for immediate danger.",
    steps: [
      "Is anything still burning or smoldering?",
      "Is everyone safe and out of danger?",
      "How was s/he burned/injured?",
      "Is s/he completely alert?",
      "Is s/he having any difficulty breathing?",
      "Does s/he have any difficulty speaking/crying between breaths?",
      "What parts of the body were burned/injured?",
      "When did this happen?",
      "Were all key questions asked in order?",
    ],
  },
  {
    id: "8",
    title: "Carabon Monoxide / Inhalation / Hazmat / CBRN",
    description:
      "Ensure safety from hazardous materials and assess patient's respiratory status.",
    steps: [
      "Is everyone safe and out of danger?",
      "What kind of chemicals/fumes or Hazmat is involved?",
      "Where are the chemicals/fumes coming from?",
      "Is s/he contaminated with chemicals?",
      "Is s/he completely alert?",
      "Is s/he having any difficulty breathing?",
      "Does s/he have any difficulty speaking/crying between breaths?",
      "Were all key questions asked in order?",
    ],
  },
  {
    id: "9",
    title: "Cardiac or Respiratory Arrest / Death",
    description:
      "Determine if patient is beyond help and if resuscitation efforts should be initiated.",
    steps: [
      "Tell me please, why does it look like s/he's dead?",
      "Do you think s/he is beyond any help?",
      "Are you certain we should not try to resuscitate him/her?",
      "Were all key questions asked in order?",
    ],
  },
  {
    id: "10",
    title: "Chest Pain / Chest Discomfort (Non-Traumatic)",
    description:
      "Assess chest pain, related symptoms, and history of heart problems.",
    steps: [
      "Is s/he completely alert?",
      "Is s/he breathing normally?",
      "Does s/he have any difficulty speaking/crying?",
      "Is s/he changing color?",
      "Describe the color change?",
      "Is s/he clammy or having cold sweats?",
      "Has s/he ever had a heart attack or angina?",
      "Has s/he take any drugs or medications in the past 12 hours?",
      "Were all key questions asked in order?",
    ],
  },
  {
    id: "11",
    title: "Choking",
    description:
      "Assess the severity of choking and the patient's current status.",
    steps: [
      "Is s/he completely alert?",
      "Is s/he breathing normally?",
      "Is s/he able to talk/cry?",
      "What did s/he choke on?",
      "Were all key questions asked in order?",
    ],
  },
  {
    id: "12",
    title: "Convulsions / Seizures",
    description:
      "Gather details on the seizure event and patient's medical history.",
    steps: [
      "Has s/he had more than one seizure in a row?",
      "Was s/he alert between the seizures?",
      "Is she pregnant?",
      "Is s/he diabetic?",
      "Is s/he epileptic?",
      "Does s/he have a history of STROKE or brain tumor?",
      "Has the jerking stopped yet?",
      "Okay, is s/he breathing right now?",
      "Agonal Breathing Test done",
      "Is s/he completely alert?",
      "Okay, is s/he breathing right now?",
      "Agonal Breathing Test done",
      "Were all key questions asked in order?",
    ],
  },
  {
    id: "13",
    title: "Diabetic Problems",
    description:
      "Assess the mental status and breathing of a patient with diabetic problems.",
    steps: [
      "Is s/he completely alert?",
      "Is s/he behaving normally now?",
      "Is s/he breathing normally?",
      "Were all key questions asked in order?",
    ],
  },
  {
    id: "14",
    title: "Drowning / Near Drowning / Diving / SCUBA Accident",
    description:
      "Determine patient's location, injuries, and vital signs after a water incident.",
    steps: [
      "Where is s/he right now?",
      "Does s/he have any injuries?",
      "Is s/he completely alert?",
      "Is s/he breathing normally?",
      "Were all key questions asked in order?",
    ],
  },
  {
    id: "15",
    title: "Electrocution / Lighting",
    description:
      "Ensure patient safety from electrical source and check for secondary injuries.",
    steps: [
      "Has the power been turned off?",
      "Is s/he disconnected from the power?",
      "Where is s/he right now?",
      "Is anything still on fire?",
      "Did s/he fall off something when this happened?",
      "How far did s/he fall?",
      "Is s/he completely alert?",
      "Is s/he breathing normally?",
      "Were all key questions asked in order?",
    ],
  },
  {
    id: "16",
    title: "Eye Problems / Injuries",
    description:
      "Assess the nature and severity of eye injuries.",
    steps: [
      "Is s/he completely alert?",
      "How did this happen?",
      "Is the eyeball cut open or is fluid leaking out of it?",
      "Were all key questions asked in order?",
    ],
  },
  {
    id: "17",
    title: "Falls",
    description:
      "Gather details about the fall, check for serious bleeding and other injuries.",
    steps: [
      "How far did s/he fall?",
      "What caused the fall?",
      "Is there any SERIOUS bleeding?",
      "Is s/he completely alert?",
      "What part of the body was injured?",
      "Is s/he having any difficulty breathing?",
      "Is it obviously bent out of shape?",
      "When did this happen?",
      "Is s/he still on the floor/ground?",
      "Were all key questions asked in order?",
    ],
  },
  {
    id: "18",
    title: "Headache",
    description:
      "Evaluate headache for signs of stroke or other serious conditions.",
    steps: [
      "Is s/he completely alert?",
      "Is s/he breathing normally?",
      "Is s/he able to talk normally?",
      "Was there a sudden onset of severe pain?",
      "Does s/he have any numbness or paralysis?",
      "Has s/he had a recent change in behavior?",
      "Exactly when did these symptoms start?",
      "When was the last time s/he was seen to be normal?",
      "Stroke Diagnostic completed?",
      "Were all key questions asked in order?",
    ],
  },
  {
    id: "19",
    title: "Heart Problems / A.I.C.D.",
    description:
      "Assess heart problems, vital signs, and history of cardiac events.",
    steps: [
      "Is s/he completely alert?",
      "Is s/he breathing normally?",
      "Does s/he have difficulty speaking/crying between breaths?",
      "Is s/he changing color?",
      "Describe the color change?",
      "Is s/he clammy or having cold sweats?",
      "Does s/he have a history of heart problems?",
      "Did it fire in the last 30 Mins?",
      "Does s/he have chest pain or chest discomfort?",
      "Did s/he take any drugs or medications in the past 12 hours?",
      "I'm going to tell you how to check her/his pulse.",
      "Were all key questions asked in order?",
    ],
  },
  {
    id: "20",
    title: "Heat / Cold Exposure",
    description:
      "Assess for complications related to temperature exposure and patient history.",
    steps: [
      "Does s/he have chest pain or chest discomfort?",
      "Is s/he completely alert?",
      "Has s/he ever had a heart attack or angina?",
      "Does s/he have a change in skin color?",
      "What is her/his skin temp?",
      "Were all key questions asked in order?",
    ],
  },
  {
    id: "21",
    title: "Hemorrhage / Lacerations",
    description:
      "Determine the source and severity of bleeding and patient's vital signs.",
    steps: [
      "Where is s/he bleeding from?",
      "Is s/he completely alert?",
      "Is s/he breathing normally?",
      "Is the blood spurting or pouring out?",
      "Is the bleeding SERIOUS?",
      "Does s/he have a bleeding disorder or is s/he on blood thinners",
      "Were all key questions asked in order?",
    ],
  },
  {
    id: "22",
    title: "Inaccessible Incident / Other Entrapments (Non-Traffic)",
    description:
      "Identify dangers, potential entrapment, and challenges for emergency access.",
    steps: [
      "Does the incident involve the release of any hazmat?",
      "Is s/he still trapped?",
      "Are there any obvious injuries?",
      "What part of the body is trapped?",
      "Where exactly is s/he?",
      "Where was s/he last seen?",
      "What is her/his approx. distance from the ground?",
      "Is the immediate area dangerous or hazardous?",
      "Will we have any problems easily reaching him/her?",
      "What problems will we have?",
      "Were all key questions asked in order?",
    ],
  },
  {
    id: "23",
    title: "Overdose / Poisoning (Ingestion)",
    description:
      "Determine intent, check for violence, and gather details about the substance ingested.",
    steps: [
      "Was this accidental or intentional?",
      "Is s/he violent?",
      "Does s/he have a weapon?",
      "Is s/he changing color?",
      "Describe the color change.",
      "Is s/he completely alert?",
      "Is s/he breathing normally?",
      "What did s/he take?",
      "When did s/he take it?",
      "Were all key questions asked in order?",
    ],
  },
  {
    id: "24",
    title: "Pregnancy / Childbirth / Miscarriage",
    description:
      "Assess stage of pregnancy, contractions, and check for complications.",
    steps: [
      "How many weeks pregnant is she?",
      "Can you see any part of the baby now?",
      "Is she having contractions?",
      "Is this her first delivery?",
      "How many minutes apart are the contractions?",
      "Does she have abdominal pain?",
      "Is there any SERIOUS bleeding?",
      "Does she have any HIGH RISK complications?",
      "Were all key questions asked in order?",
    ],
  },
  {
    id: "25",
    title: "Psychiatric / Abnormal behavior / Suicide Attempt",
    description:
      "Assess for patient and caller safety, intent of self-harm, and patient's vital status.",
    steps: [
      "Is s/he violent?",
      "Does s/he have a weapon?",
      "Where is s/he right now?",
      "Is this a suicide attempt?",
      "Is s/he thinking about committing suicide?",
      "Where is s/he cut?",
      "Is there any SERIOUS bleeding?",
      "Is s/he completely alert?",
      "Does s/he have difficulty breathing?",
      "Were all key questions asked in order?",
    ],
  },
  {
    id: "26",
    title: "Sick Person (Specific Diagnosis)",
    description:
      "Determine patient's current status and check for immediate threats to life.",
    steps: [
      "Is s/he completely alert?",
      "Is s/he breathing normally?",
      "Is s/he bleeding or vomiting blood?",
      "Does s/he have any pain?",
      "Were all key questions asked in order?",
    ],
  },
  {
    id: "27",
    title: "Stab / Gunshot / Penetrating Trauma",
    description:
      "Assess the severity of penetrating trauma, check for serious bleeding, and safety.",
    steps: [
      "Do you think s/he is beyond any help?",
      "Is the assailant still nearby?",
      "Is there any SERIOUS bleeding?",
      "Is s/he completely alert?",
      "What part of the body was injured?",
      "Is there more than one wound?",
      "When did this happen?",
      "Were all key questions asked in order?",
    ],
  },
  {
    id: "28",
    title: "Stroke (CVA) / Transient Ischemic Attack (TIA)",
    description:
      "Perform stroke diagnostic and determine the time of symptom onset.",
    steps: [
      "Is s/he completely alert?",
      "Is s/he breathing normally?",
      "Tell me why you think it's a stroke.",
      "Stroke Diagnostic used.",
      "Exactly what time did these symptoms start?",
      "When was the last time s/he was seen to be normal?",
      "Has s/he ever had a STROKE before?",
      "Were all key questions asked in order?",
    ],
  },
  {
    id: "29",
    title: "Traffic / Transportation Incidents",
    description:
      "Assess for vehicle hazards, entrapment, and patient injuries.",
    steps: [
      "Are there any chemicals or other Hazmat involved",
      "Is anyone pinned?",
      "Was anyone thrown from the vehicle?",
      "Does everyone appear to be completely awake?",
      "Okay, is s/he breathing right now?",
      "Is her/his breathing noisy?",
      "Are there any obvious injuries?",
      "Is there any SERIOUS bleeding?",
      "Were all key questions asked in order?",
    ],
  },
  {
    id: "30",
    title: "Traumatic Injuries (Specific)",
    description:
      "Check for serious bleeding and specific injuries following trauma.",
    steps: [
      "Is there any SERIOUS bleeding?",
      "Is s/he completely alert?",
      "What part of the body was injured?",
      "Is s/he having any difficulty breathing?",
      "Is it obviously bent out of shape?",
      "Have the parts been found?",
      "When did this happen?",
      "Were all key questions asked in order?",
    ],
  },
  {
    id: "31",
    title: "Unconscious / Fainting (Near)",
    description:
      "Assess breathing and consciousness status, checking for potential complications.",
    steps: [
      "Is her/his breathing completely normal?",
      "Agonal Breathing Test done?",
      "Is s/he still unconscious?",
      "Is s/he completely alert?",
      "Is s/he changing color?",
      "Describe the color change.",
      "Does s/he have a history of heart problems?",
      "Does she have abdominal pain?",
      "Were all key questions asked in order?",
    ],
  },
  {
    id: "32",
    title: "Unknown Problem (Person Down)",
    description:
      "Determine the patient's state of consciousness and location.",
    steps: [
      "Does s/he appear to be completely awake?",
      "Did you ever hear her/him talk/cry?",
      "What is s/he doing - standing, sitting or lying down?",
      "Is s/he moving at all?",
      "Where exactly is s/he?",
      "Were all key questions asked in order?",
    ],
  },
  {
    id: "33",
    title: "Tranfer / Interfacility / Palliative Care",
    description:
      "Gather information for patient transfer, focusing on condition and necessary resources.",
    steps: [
      "Is this call a result of an evaluation by a nurse or doctor?",
      "Is s/he completely alert?",
      "Is s/he breathing normally?",
      "Is this a sudden/unexpected change in their usual condition?",
      "Does s/he have any significant bleeding?",
      "Does s/he have any shock symptoms?",
      "Is s/he in severe pain?",
      "Could this be a MI?",
      "Will any special equipment be necessary?",
      "Will additional personnel be necessary?",
      "What type of Personnel is required?",
      "What's the name of the referring doctor?",
      "What's the name of the responsible RN?",
      "What's the name of the patient?",
      "What's your fax number?",
      "Were all key questions asked in order?",
    ],
  },
];

const ProtocolBook = () => {
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedProtocol, setSelectedProtocol] = useState<null | typeof protocols[0]>(null);

  // Filter protocols by title
  const filteredProtocols = protocols.filter((protocol) =>
    protocol.title.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <div className="p-4 md:p-8 max-w-6xl mx-auto min-h-screen bg-white">
      <h1
        className="text-4xl font-extrabold mb-6 pb-2 border-b-4"
        style={{ color: PRIMARY_NAVY, borderColor: PRIMARY_NAVY + "30" }}
      >
        <span className="text-3xl mr-2 align-middle"></span> EMS Protocol Reference
      </h1>

      {/* Search input */}
      <input
        type="text"
        placeholder="Search protocols..."
        value={searchQuery}
        onChange={(e) => setSearchQuery(e.target.value)}
        className="w-full p-3 mb-6 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
      />

      {/* Grid of protocol cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-4">
        {filteredProtocols.map((protocol) => (
          <div
            key={protocol.id}
            className="p-4 shadow-lg rounded-lg cursor-pointer hover:shadow-xl transition bg-white"
            onClick={() => setSelectedProtocol(protocol)}
          >
            <h2 className="font-bold text-lg mb-2">{protocol.title}</h2>
            <p className="text-gray-500 text-sm line-clamp-3">{protocol.description}</p>
          </div>
        ))}

        {filteredProtocols.length === 0 && (
          <p className="text-gray-500 col-span-full text-center">No protocols found for "{searchQuery}"</p>
        )}
      </div>

      {/* selected protocol */}
      {selectedProtocol && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
          <div className="bg-white rounded-lg max-w-3xl w-full p-6 relative shadow-2xl overflow-y-auto max-h-[90vh]">
            <button
              className="absolute top-3 right-3 text-gray-500 hover:text-gray-700 text-xl font-bold"
              onClick={() => setSelectedProtocol(null)}
            >
              ✖
            </button>

            <h2 className="text-2xl font-bold mb-2" style={{ color: PRIMARY_NAVY }}>
              {selectedProtocol.title}
            </h2>
            <p className="text-gray-700 italic mb-4 border-l-4 pl-3 py-1" style={{ borderColor: PRIMARY_NAVY }}>
              {selectedProtocol.description}
            </p>

            <div className="space-y-2">
              {selectedProtocol.steps.map((step, idx) => (
                <div
                  key={idx}
                  className="flex items-start bg-gray-50 p-3 shadow-inner rounded-md border border-gray-200"
                >
                  <span
                    className="flex-shrink-0 w-8 h-8 flex items-center justify-center text-white font-extrabold rounded-full mr-3 text-sm"
                    style={{ backgroundColor: PRIMARY_NAVY }}
                  >
                    {idx + 1}
                  </span>
                  <p className="text-gray-800 font-medium leading-relaxed flex-grow">{step}</p>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default ProtocolBook;