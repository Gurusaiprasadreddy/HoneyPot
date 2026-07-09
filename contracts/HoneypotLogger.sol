// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract HoneypotLogger {
    struct AttackLog {
        string timestamp;
        string ip;
        string sessionId;
        string commands;
        string attackType;
        uint8 riskScore;
        string sha256Hash;
    }

    mapping(string => AttackLog) public logs;
    string[] public logHashes;

    event LogStored(string indexed sha256Hash, string attackType, uint8 riskScore);

    function storeLog(
        string memory _timestamp,
        string memory _ip,
        string memory _sessionId,
        string memory _commands,
        string memory _attackType,
        uint8 _riskScore,
        string memory _sha256Hash
    ) public {
        require(bytes(logs[_sha256Hash].sha256Hash).length == 0, "Log already exists");

        logs[_sha256Hash] = AttackLog({
            timestamp: _timestamp,
            ip: _ip,
            sessionId: _sessionId,
            commands: _commands,
            attackType: _attackType,
            riskScore: _riskScore,
            sha256Hash: _sha256Hash
        });

        logHashes.push(_sha256Hash);

        emit LogStored(_sha256Hash, _attackType, _riskScore);
    }

    function verifyLog(string memory _sha256Hash) public view returns (bool) {
        return bytes(logs[_sha256Hash].sha256Hash).length != 0;
    }

    function getLog(string memory _sha256Hash) public view returns (
        string memory timestamp,
        string memory ip,
        string memory sessionId,
        string memory commands,
        string memory attackType,
        uint8 riskScore
    ) {
        AttackLog memory l = logs[_sha256Hash];
        return (l.timestamp, l.ip, l.sessionId, l.commands, l.attackType, l.riskScore);
    }
}
