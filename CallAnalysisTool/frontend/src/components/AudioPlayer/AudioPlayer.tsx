// imports
import styles from "./AudioPlayer.module.css"
import { FaStepBackward } from "react-icons/fa";
import { FaStepForward } from "react-icons/fa";
import { FaPlay } from "react-icons/fa";
import { FaPause } from "react-icons/fa";
import { useState, useRef, useEffect } from 'react'

// props
type AudioPlayerProps = {
    path?: string,
    onProgress?: (time: number) => void
}

function AudioPlayer({ path, onProgress }: AudioPlayerProps) {

    // states
    const [isPlaying, setIsPlaying] = useState(false)
    const [duration, setDuration] = useState(0)
    const [currentTime, setCurrentTime] = useState(0)

    // references
    const audioPlayer = useRef<HTMLAudioElement>(null) // references audio component
    const progressBar = useRef<HTMLInputElement>(null) // references progress bar
    const animationRef = useRef<number>(0) // referenced knobby animation

    // handles duration change when file changes
    useEffect(() => {

        // sets duration after change
        const handleDurationChange = () => {
            const duration = Math.floor(audioPlayer.current!.duration || 0)
            setDuration(duration)
            progressBar.current!.max = duration.toString()
        }

        // listens for file change
        audioPlayer.current!.addEventListener('loadedmetadata', handleDurationChange)
        audioPlayer.current!.addEventListener('durationChange', handleDurationChange)

        // removing listeners
        return () => {
            if (audioPlayer.current) {
                audioPlayer.current!.removeEventListener('loadedmetadata', handleDurationChange)
                audioPlayer.current!.removeEventListener('durationChange', handleDurationChange)
            }
        }
    }, [])

    // resets UI whenever the file changes
    useEffect(() => {
        // stop animation + pause
        cancelAnimationFrame(animationRef.current)
        setIsPlaying(false)

        if (audioPlayer.current) {
            audioPlayer.current.pause()
            audioPlayer.current.currentTime = 0
        }

        // reset slider + time + duration
        setCurrentTime(0)
        setDuration(0)
        if (progressBar.current) {
            progressBar.current.value = "0"
            progressBar.current.max = "0"
            progressBar.current.style.setProperty("--seek-before-width", "0%")
        }
    }, [path])


    // calculates intended time format
    const formatTime = (secs: number) => {
        const minutes = Math.floor(secs / 60);
        const returnedMinutes = minutes < 10 ? `0${minutes}` : `${minutes}`
        const seconds = Math.floor(secs % 60)
        const returnedSeconds = seconds < 10 ? `0${seconds}` : `${seconds}`
        return `${returnedMinutes}:${returnedSeconds}`
    }

    // toggles the play/pause state
    const togglePlayPause = () => {

        const prevValue = isPlaying
        setIsPlaying(!prevValue)

        if (!prevValue) {
            audioPlayer.current!.play()
            animationRef.current = requestAnimationFrame(whilePlaying)
        }
        else {
            audioPlayer.current!.pause()
            cancelAnimationFrame(animationRef.current)
        }
    }

    // toggles animation for knobby while playing
    const whilePlaying = () => {
        progressBar.current!.value = audioPlayer.current!.currentTime.toString();
        progressBar.current!.style.setProperty("--seek-before-width", `${Number(progressBar.current!.value) / duration * 100}%`)
        setCurrentTime(Number(progressBar.current!.value))
        if (onProgress) {
            onProgress(Number(progressBar.current!.value));
        }
        animationRef.current = requestAnimationFrame(whilePlaying)
    }

    // changes the range slider
    const changeRange = () => {
        audioPlayer.current!.currentTime = Number(progressBar.current!.value);
        progressBar.current!.style.setProperty("--seek-before-width", `${Number(progressBar.current!.value) / duration * 100}%`)
        setCurrentTime(Number(progressBar.current!.value))
        if (onProgress) {
            onProgress(Number(progressBar.current!.value));
        }
    }

    // skips the playback back 10
    const backTen = () => {
        progressBar.current!.value = (Number(progressBar.current!.value) - 10).toString()
        changeRange()
    }

    // skips the playback forward 10
    const forwardTen = () => {
        progressBar.current!.value = (Number(progressBar.current!.value) + 10).toString()
        changeRange()
    }

    return (
        <div className={styles.audioPlayer}>

            {/* progress bar */}
            <div className={styles.progressBarWrapper}>
                <input className={styles.progressBar} type="range" defaultValue="0" ref={progressBar} onChange={changeRange}></input>
            </div>

            {/* control bar*/}
            <div className={styles.controlBar}>

                {/* buttons */}
                <audio ref={audioPlayer} src={path}></audio>
                <button className={styles.forwardBackward} onClick={backTen}><FaStepBackward /></button>
                <button className={styles.playPause} onClick={togglePlayPause} aria-label={isPlaying ? 'Pause' : 'Play'}>
                    {isPlaying ? <FaPause /> : <FaPlay />}
                </button>
                <button className={styles.forwardBackward} onClick={forwardTen}><FaStepForward /></button>

                {/* current time */}
                <div className={styles.currentTime}>{formatTime(currentTime)}/</div>

                {/* duration */}
                <div className={styles.duration}>{formatTime(duration)}</div>
            </div>
        </div>
    )
}

export { AudioPlayer } 