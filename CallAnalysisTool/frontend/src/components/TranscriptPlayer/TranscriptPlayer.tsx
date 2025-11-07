'use client'
import styles from "./TranscriptPlayer.module.css"
import { useRef, useEffect } from "react";

function TranscriptPlayer({ transcriptData, currentTime }) {

    // references
    const chatBoxRef = useRef(0)

    // converts json into message
    const segments = transcriptData?.segments ?? []
    const messages = segments.map((segment, index) => ({
        id: index,
        speaker: segment.speaker || "unknown",
        text: segment.text ? segment.text.trim() : "",
        start: segment.start,
        end: segment.end,
    }))

    // finds active message based on current time
    let activeIndex = messages.findIndex(
        message => currentTime >= message.start && currentTime <= message.end
    )

    // addresses active index during gaps in time stamps
    if (activeIndex === -1) {
        // use the last message before the gap
        for (let i = messages.length - 1; i >= 0; i--) {
            if (currentTime > messages[i].end) {
                activeIndex = i
                break
            }
        }

        // edge case (before first index)
        if (activeIndex === -1) {
            activeIndex = 0
        }
    }

    // reset scroll/activeChat when transcript changes
    useEffect(() => {
        const box = chatBoxRef.current
        if (box) {
            box.scrollTop = 0
            activeIndex = 0
        }
    }, [transcriptData])


    // return empty chat box if no transcript has been loaded
    if (segments.length === 0) {
        return <div className={styles.chatBox}>Choose a call to review</div>;
    }

    return (
        <div className={styles.chatBox}>
            <div ref={chatBoxRef} className={styles.chatInner}>
                {messages.map(message => (
                    <div
                        key={message.id}
                        className=
                        {`
                            ${styles.messageRow} 
                            ${message.speaker === "caller" ? styles.right : styles.left}
                        `}
                    >
                        <div
                            className=
                            {`
                                ${styles.bubble} 
                                ${message.speaker === "caller" ? styles.callerBubble : styles.dispatcherBubble}
                                ${message.id === activeIndex ? styles.activeBubble : ""} 
                            `}
                        >
                            <div className={styles.speaker}>
                                {message.speaker}
                            </div>
                            <div>
                                {message.text}
                            </div>
                        </div>
                    </div>
                ))}
            </div>
        </div>
    )
}

export { TranscriptPlayer }