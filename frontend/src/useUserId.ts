import { useEffect, useState } from "react";

function createRandomId(){
    if (crypto.randomUUID){
        return crypto.randomUUID();
    }
    return Math.random().toString(36).slice(2);
}

export function useUserId() {
    const [userId, setUserId] = useState<string | null>(null);

    useEffect(() => {
        let storedUserId = localStorage.getItem("userId");
        if (!storedUserId) {
            storedUserId = createRandomId();
            localStorage.setItem("userId", storedUserId);
        }
        setUserId(storedUserId);
    }, []);
    return userId;
}