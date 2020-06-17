// ==UserScript==
// @name         AoPSCoin
// @namespace    http://tampermonkey.net/
// @version      0.8
// @description  Client-side code for AoPSCoin. Please know that this is still in development and all data shown is just an example
// @author       casi
// @match        https://artofproblemsolving.com/*
// @grant        none
// @run-at document-start
// ==/UserScript==

setTimeout(function() {
    'use strict'; // Default from tampermonkey
    var myUsername = AoPS.bootstrap_data.my_profile.username
    // Remove the old feed and construct a new one with the AoPSCoin tab
    $("#feed-wrapper").remove()
    AoPS.Feed.constructFeed()
    AoPS.Feed.feed_view.global_subfeed = AoPS.Feed.feed_view.addSubfeed({
        header_text: "AoPSCoin", // The header for inside the feed
        id: "feed-aopscoin-tab", // HTML ID
        title: "AoPSCoin", // Title for hovering over the button
        icon_letter: "y", // I'm using the impossible cube logo for now
        category: new AoPS.Community.Models.CategoryFeedTopics({ // Create the category so the feed can open when we click the cube icon.
            master: AoPS.Feed.feed_view.community_master, // We're using the CategoryFeedTopics, because it won't keep loading new posts like CategoryGlobal
        }),
        master: AoPS.Feed.feed_view.community_master // The master was created on the constructFeed()
    });

    function elapsedTime (time) { // This is for less than or equal to 6 hours ago
        if (time <= 60000) {return ("a few seconds ago")} // For less than a minute
        else if (time <= 3540000) { // For 1 minute - 59 minutes
            let minutes = Math.round(time/60000) // Get the number of minutes
            if (minutes == 1) {return ("1 minute ago")} // 1 minute since the English Language won't let me plug it into the other formula
            else {return (minutes.toString() + " minutes ago")} // x minutes ago
        }
        else { // For any other time given (1 hour - 6 hours)
            let hours = Math.round(time/3600000); // Get the number of hours
            if (hours == 1) {return ("1 hour ago")} // 1 hour in the singular
            else {return (hours.toString() + " hours ago")}; // x hours ago
        }
    }
    function meridian (hour, minute) { // For AM and PM
        minute = minute.toString();
        if (minute.length == 1) {minute = "0" + minute} // Turns 9:5 into 9:05
        if (hour == 0) {return ("12:" + minute + " AM")} // 12 AM
        else if (hour < 12) {return (hour.toString() + ":" + minute + " AM")} // 1 AM - 11 AM
        else if (hour == 12) {return ("12:" + minute + " PM")} // 12 PM
        else {return((hour-12).toString() + ":" + minute + " PM")} // 1 PM - 11 PM
    }
    function dateFormat (time) { // NOTE: This takes anything, Dates, times, milliseconds since 1970, etc.
        var months = ["January","February","March","April","May","June","July","August","September","October","November","December"] // Month list, this is global
        // Format date
        let now = new Date()
        let date = new Date(time)
        let day = date.getDate()
        let month = months[date.getMonth()]
        let year = date.getFullYear()
        let hour = date.getHours()
        let minute = date.getMinutes()
        let theday;
        //Print based on today, yesterday, or else
        if (day == now.getDate()) {theday = "Today"} // Check if the date posted was today
        else if (day == (now.getDate() - 1)) {theday = "Yesterday"} // Check if the date posted was yesterday
        else {theday = (month + " " + day + ", " + year)} // Otherwise, format as July 4, 1776
        return (theday + " at " + meridian(hour,minute)) // e.g. July 4, 1776 at 9:30 AM
    }
    function formatTime (date) { // Master function for the time formatting
        let nowDate = new Date(); // Get the date now
        let thenDate = new Date(date); // Make the input into a date

        // Get time since now and the posting time
        let then = thenDate.getTime();
        let now = nowDate.getTime();
        let timeElapsed = now - then;

        if (timeElapsed <= 21600000) {return (elapsedTime (timeElapsed))} // If it's less than or equal to 6 hours, use the elapsed time module
        else {return dateFormat(date)} // Otherwise, just post the date sent
    }
    function submitNewTransaction(to,from,amount,notes) {
        console.log(amount.toString() + " AoPSCoins from " + from + " to " + to + ". Notes: " + notes)
    }
    function checkTransactionUIError() { // Checks for errors in the transactionUI before submitting
        // There has to be a username submitted and verified by AoPS
        if ($(".cmty-itemlist-username").length <= 0) {
            alert("User invalid")
            return false;
        }
        let amount = $(".cmty-subject-input")[0].value
        // Number must be a positive integer. Make sure to run these checks at the back end too in case people modify the code
        if(Math.floor(amount) == amount && $.isNumeric(amount) && amount > 0) {}
        else {
            alert("Amount invalid")
            return false;
        }
        return true;
    }
    function transactionUI() { // Setting up the transaction UI
        // Use the PM template by creating a new private conversation
        new AoPS.Community.Views.NewPrivateConversation({
            category_name: "",
            category_id: 1,
            model: AoPS.Feed.community_master.fetchCategory(1),
            master: AoPS.Feed.community_master
        })
        // Set up the button and override all existing functions
        $(".cmty-submit-button").on("click",function (e) { // Just onclick, I don't want right-clicks triggering it
            e.stopPropagation() // This makes the button completely dead
            if(checkTransactionUIError()) { // First run a check to make sure everything is acceptable.
                $(".cmty-itemlist-username").each(function (object) { // Go through ever username on the list
                    // Button code:
                    // Submit a new transaction, which is submitNewTransaction(to,from,amount,notes)
                    // to = $(this)[0].innerText.slice(0,-2)
                    // from = myUsername (we took this from the bootstrap data at the beginning, it's AoPS.bootstrap_data.my-profile.username
                    // amount = parseInt($(".cmty-subject-input")[0].value), which takes the value from the amount input and turns it into an integer
                    // notes = $(".cmty-post-textarea")[0].value
                    submitNewTransaction($(this)[0].innerText.slice(0,-2),myUsername,parseInt($(".cmty-subject-input")[0].value),$(".cmty-post-textarea")[0].value)
                    $(".aops-close-x").click() // Close the window
                    // This fixes a weird bug where the keyboard shortcut triggers
                    setTimeout(function () {
                        $(".aops-close-x").click()
                    },10);
                })
            }
        });
        $(document).on("keydown", function(e) {
            var key_pressed = e.which || e.keyCode;
            if (key_pressed === 13 && (e.ctrlKey || e.metaKey)) {
                console.log("pressed")
                e.stopPropagation()
                $(".cmty-submit-button").trigger("click")
            }
        });
        // Formatting
        $(".cmty-tags-line").remove() // No tags (maybe future feature)
        $(".cmty-bbcode-buttons").remove() // No buttons (maybe future feature)
        $(".cmty-posting-preview-bar").remove() // No preview bar (will reimplement when buttons are implemented)
        $(".cmty-post-preview").remove() //Remove preview
        $(".cmty-posting-subject-line .cmty-heading-text").text("Amount") // Rename "Subject" to "Amount"
        $(".aops-modal-frame").css("background-color","#666") // I can't make the modal frame smaller, so I just make it look cooler
        $(".cmty-post-textarea").attr("placeholder","Notes") // Add a notes placeholder so users know what it is


    }
    function setFeedHeader() {
        let feedHeader = $("#feed-aopscoin-tab .feed-subfeed-header") // Get the header
        feedHeader.html(`<span class="feed-subfeed-title">AoPSCoin</span>
		<span class="feed-subfeed-header-right">
			<span title="Start New Transaction" id="new-transaction" class="aops-font">V</span>
			<span title="Close feed" class="aops-font feed-close">J</span>
		</span>`); // Add HTML
        $("#feed-aopscoin-tab #new-transaction").mousedown(function () { // Override the other functions with mousedown
            transactionUI() // When clicked, open up the UI
        });
    }
    function setFeedTopics (transactions) { // Function for formatting and constructing feed. This takes a list of objects {name:"",amount:"",reason:"",timestamp: Date(),notes:""}
        let feedList = $("#feed-aopscoin-tab .aops-scroll-content") // This is where the feed content will go
        feedList.text("") // Clear the existing feed to get rid of previous loads and the No More Topics text AoPS adds
        transactions.sort(function(a, b) {var dateA = new Date(a.timestamp), dateB = new Date(b.timestamp);return dateA - dateB;}); // Function I found online to sort the transactions by date
        transactions.sort().reverse() // Sort the transactions by date from newest to oldest
        var transaction;
        for (transaction of transactions) { // Go through all the transactions
            // Set up the variables for simplicity
            let name = transaction.name
            let amount = transaction.amount
            let time = formatTime(transaction.timestamp)
            let notes = transaction.notes
            // Some formatting to show whether the transaction was sent or received
            if (transaction.received) {name = ("From " + name)}
            else {name = ("To " + name)}
            // Add the HTML with the variables added
            feedList.append(`<div class="cmty-topic-cell" title="` + amount + `">
<div class="cmty-topic-cell-left"><div class="cmty-color-main cmty-topic-cell-jump-to-bottom" style="color: rgb(53, 108, 181);"></div>
            <div class="cmty-color-main cmty-topic-cell-goto-unread" style="color: rgb(53, 108, 181);">
                <div title="Jump to first unread" class="aops-font">h&nbsp;</div></div>
            <div class="cmty-topic-cell-second-row"><span class="cmty-color-main cmty-topic-cell-username" data-hj-suppress="" data-hj-masked="" style="color: rgb(53, 108, 181);">` + name + `</span>  &nbsp; </span><span style="float:right;margin-right: 3px;margin-left: 3px;font-family:AoPS;font-style:normal;box-sizing: border-box;color: rgb(53, 108, 181);">y</span> <span class="aopscoin-amount" style="float:right;margin-left:4px;color: rgb(53, 108, 181);">` + amount + `
                <span class="cmty-topic-cell-watchers"></span></div>
                <div class="cmty-topic-cell-subtitle"><div class="cmty-topic-cell-subtitle-left">
                <span class="aops-font">N</span>
            <span class="cmty-topic-cell-time cmty-reply-time">` + time + `</span></div></div>
<div class="cmty-topic-cell-post">` + notes + `
			</div>
        </div></div>`);
        }
    }
    $("#feed-aopscoin-tab").on("click",function() { // Listener for when the user clicks the tab toggler
        setTimeout(function () {
            if ($("#feed-wrapper").attr("class") == "feed-open") { // Backup for when the user closes the feed by clicking the tab toggler
                let transactions = [{name:"casi",amount:"20",received:true,timestamp: new Date("October 13, 2014 11:13:00"),notes: "These are notes"},
                                    {name:"casi",amount:"100",received:false,timestamp: new Date("June 7, 2020 14:05:00"),notes: "Free money!"},
                                    {name:"RYang2",amount:"20",received:false,timestamp: new Date("June 7, 2020 14:00:00"),notes: "These are notes"},
                                    {name:"casi",amount:"20",received:true,timestamp: new Date("June 7, 2020 13:05:00"),notes: "These are notes"},
                                    {name:"rrusczyk",amount:"100",received:true,timestamp: new Date("June 6, 2020 14:05:00"),notes: "Free money!"},
                                    {name:"LauraZed",amount:"2000",received:true,timestamp: new Date("October 13, 2018 11:13:00"),notes: "Just another bit of money from the site admins"},
                                    {name:"casi",amount:"2000",received:true,timestamp: new Date("October 13, 2017 11:13:00"),notes: "IDK why I'm giving you 2000"},
                                    {name:"RYang2",amount:"2000",received:false,timestamp: new Date("October 13, 2016 11:13:00"),notes: "Shhhhhhh....."},
                                    {name:"rrusczyk",amount:"2000",received:true,timestamp: new Date("October 13, 2015 11:13:00"),notes: "From the site ninjas"},
                                    {name:"casi",amount:"2000",received:false,timestamp: new Date("October 13, 2014 11:13:00"),notes: "Hi there. Here's some money!"}]
                setFeedTopics(transactions) // Set the feed as the transactions
                setFeedHeader()
            };
        },300) // If this runs too fast, the feed isn't open yet and nothing happens. 300 milliseconds works.
    });
},4000); // Run 4 seconds after initial load, I haven't found a way to automate this
