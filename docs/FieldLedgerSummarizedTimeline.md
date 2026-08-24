# FieldLedger Summarized Timeline

> General things I need to include:
>
> * When did I work on cleaning and organizing those points in QGIS?
> * When did I work on that QGIS plugin that didn't go anywhere?
> * When did I talk to each person and what did I learn from it?
> * When did I start the sync UI?

## 2024

### 2024.02 Feb

Started as an hourly. Talked with Dr. Davis and Dr. Heaton. Got access to Killian's data and the Box folder with historical data.

I started on a number of Corsera courses provided by Dr. Martin to learn about GIS tools and using python with spatial data.

### 2024.03 Mar

I worked my way through a couple of example projects using QGIS and different database providers. I found that a lot of spatial database projects used PostgreSQL + PostGIS, but I also explored other options. I also looked at different tools for things like APIs in different languages, but I didn't understand them very well at the time.

I had made the first version of the database schema. This was done primarily by looking through Killian's data and seeing what columns were in the spreadsheets. I extrapolated from there to see what kinds of information I thought would be important that wern't included. I also tried to take research into Regenerative agriculture into account by designing tables to support complex systems.

### 2024.04 Apr

I learned a lot about database management, using the tool pgAdmin4. I also took online courses to familiarize myself with QGIS and learned about PostGIS. I looked into a number of different tools, but these were the ones that seemed to fit the project best.

During this time, I created a simple example database to learn about the tools, and another database using the schema I designed from Killian's data. It didn't have any data in it yet, I was just working on understanding the structure.

### 2024.05 May

I had finalized the version of the database schema that was designed off of Killian's data and modified to include the rest of what I thought it needed for I-Regen. I made a simple api to go on top of it, and started to get some basic feedback on it.

This design was quite complex, but it didn't actually reflect how most farm data is stored, as it was built more on a research tool. This was very helpful for understanding what I had done well and where I needed to improve. I also think this was the point that I realized this project would be much longer-term than I initially thought.

### 2024.06 Jun

I made progress on a project that designed to ingest the spreadsheets of data that killian had formatted and reformat it so that my database design could start to take that data in. This was a fairly extensive undertaking to understand the basics of data manipulation and validation using already decent data as an input. I used a python script for this and simply output the data in .xlsx format as tables I could upload into the database.

### 2024.07 Jul

I used the example data that I had ingested into this version of the database to generate examples of what was possible so far. I used this to get feedback on the direction of the project, which helped me to understand the level of overcomplication that I had designed into the schema. My design philosophy transitioned from figuring out how to store *all* of the farm management data that might be needed for a complex system to trying to break the problem down into minimizing the database schema while still storing enough data for it to be maximally useful.

### 2024.08 Aug

### 2024.09 Sep

### 2024.10 Oct

### 2024.11 Nov

### 2024.12 Dec

## 2025

### 2025.01 Jan

Started my Master's program in Crop Science (Bioinformatics).

Enrolled in CPSC 440: Applied Statistical Method, CPSC 418: Crop Growth and Management and NRES 499: Soil Ecology.

I started a project with Jaymie Celliti properly filtering through the massive amount of inconsistently structured data in the Box folder from the South Farms. The goal is to find patterns and see what data existed there that would eventually be incorporated into the database, and make sure that future database schema versions would be set up to take in as much of that data as possible.

### 2025.02 Feb

### 2025.03 Mar

### 2025.04 Apr

### 2025.05 May

CPSC 440 helped me to understand how statistical methods inform experimental design, which has helped me understand what table columns will be important to store if the database is to be useful for researchers.

CPSC 418 Helped me to understand what a typical growing season should look like. While it didn't change much about my database design decisions, it did actually help a lot in being able to intuitively look at operations and see whether they are reasonable. This has since helped tremendously in designing common-sense validation rules to flag field operations.

NRES 499 was one of my first Soil focused classes, and the original reason I wanted to try to include soil test data in the database. While that has not progressed much since then, it did help show me my own interest in Soils and has caused me to connect with researchers like Dr. Andrew Margenot.

### 2025.06 Jun

During this tmie, I had combined the lessons I learned while designing a database schema based on Killians data with my understanding of John Deere's data and my talks with Farm Managers to create a new database schema based more on John Deere's structure than Killian's. This was an early version of this schema, and I continued to iterate as I learned more about everything. I created a completely new database in pgAdmin4 (instead of modifying the previous one) and used data from John Deere to fill it with some example data to look at and generate ideas of what FieldLedger could output.

### 2025.07 Jul

This is when I transitioned from just collecting John Deere data to look at the structure and for examples to actually trying to understand the John Deere Operations Center in detail. I started an application called MJD_Explorer that I used to make requests and explore the data structures. This is also where I started to realize just how massive an undertaking this was.

During this time, I also worked more on the project to filter through the massive box folder to see what insights I could gain from how that data is structured. This did not play much into the database design compared to the John Deere data, but it was an important part of the project to make sure things would hold up when it became time to incorporate that data.

### 2025.08 Aug

Started my second semester, enrolled in CPSC 444: Intro to Spatial Analytics, CPSC 437: Principles of Agroecology, and CPSC 594: Professional Orientation.

I spent some time on a side project with Sola Gratia Farms, mapping out a windbreak and working to become more familiar with GPS mapping and the tools in the Processing Toolbox on QGIS. This smaller project helped me a lot in understanding how to use QGIS beyond a basic level.

This is also where I finalized a new version of the schema. It was heavily based on the previous one, built on John Deere's data, but included lessons I had learned from Killian's data, the Box folder, interviews, and my understanding of data validation. My conversations with Farm Manager Darrin Joos also played heavily in choosing what data to focus on here.

### 2025.09 Sep

Started the current version of FieldLedger. This is where the current github repo starts as well.

Put into practice the FastAPI template in a way that could be connected with a frontend, and utilize Docker.

As I had done previously, I created a new version of the database. For this one, I did not use pgAdmin4 at all. While the tool was helpful for working with databases directly, I knew that I would have to transition to using a Docker container. While I could technically still use pgAdmin4 with one, it was easier to just use tools built in to vscode that work with Docker and databases.

I had chosen to use Docker for everything because I saw that many projects did this for ease of maintenance and deployment. NCSA uses this kind of stack frequently, and I knew that I would have to learn docker sooner or later. At this point, I had been reading about docker for months in preparation of this, so I would have an idea of what I was doing when I decided to transition everything to a docker-compose stack.

### 2025.10 Oct

I spent a lot of time trying to famliarize myself with John Deere's data formats and API endpoints. To be honest, it has been extremely difficult, as I started to truly realize how much data is badly generated, or poorly validated. This has also been the point where I actually understood both the imporance and difficulty of proper data validation, and how important it would be to build that as a core part of FieldLedger.

This is also the point where I started to formaize the sync protocol by trying to understand how to connect and simplify all of the John Deere data into something that was compatible with the database schema I had so far.

### 2025.11 Nov

I worked on building out my ability to take in data from John Deere, format it, and connect it to data from their other APIs (for example, getting the product from an operation and connecting it to the actutal product from the product API). This should have been straightforward, but the lack of data standardization has made this a nightmare. At this point, I had no idea whether the level of data standardization needed for FieldLedger to be useful would even be possible with John Deere's data.

### 2025.12 Dec

CPSC 444 was very helpful in designing the spatial-first foundation of my database and understanding how differnt spatial data formats worked. This has informed much of how the database will work with spatial data, and helped tremendously throughout the process of designing systems to work with that spatial data.

CPSC 437 was extremely helpful in understanding the types of systems that will be necessary to work with if FieldLedger is to enable research for Regenerative Agriculture systems. Not only that, but the understanding of these systems and Dr. Davis' approach to them has helped me to understand how to approach complex systems like that quantitatively, which has also informed the data that I have to maintain in FieldLedger.

CPSC 594 was very helpful in learning how to turn the progress I had made so far into a thesis project. At this time I was not certain whether I would attempt to make FieldLedger into the thesis project, or try to work on it at a smaller scope while doing a more traditional study for my thesis. I am thankful that I fully committed, and that my advisor, Dr. Marin, has helped me turn it into a Thesis project, even though it is unconventional.

At this point I had done a lot of research into how these systems worked, talked with stakeholders and people from NCSA and more for technical knowledge, and I felt like it was time to build off of past versions of FieldLedger by creating the final version of the database schema.

## 2026

### 2026.01 Jan

Started my third semester with CPSC 543: Applied Multivariate Statistics, and NRES 420: Restoration Ecology.

This is where I created the first tables in the newest database schema in the github repo. Before this point, I had created multiple test databases, but this was the point where I created the final version of the database that I expect to end up in production, albeit with modifications.

There have been many lessons learned from John Deere, from different interviews, and all of these were put into practice in this version of FieldLedger.

### 2026.02 Feb

### 2026.03 Mar

### 2026.04 Apr

I had gained a number of important insights about how John Deere stored their data, and used it not only to modify the database schema, but also develop the protocol for syncing data between the two platforms. Unfortunately, an offhand comment in a support email alerted me that John Deere was going to be deprecating eTags by the end of the year. eTags were the method that I had been working on for months to sync data, since they allow me to request only data that has changed since my last request. The unfortunate news that these would no longer be supported soon meant that I was forced to pivot to learning and using webhooks, and updating my sync protocol to match. The previous work I had done helped a lot in understanding the data structures I am working with, but unfortunately, webhooks function *very* differently than eTags, so there was little overlap there to work with.

### 2026.05 May

CPSC 543 furthered my understanding of statistical methods, and especially those used in systems with many variables. The types of research that I have to understand, and eventually that FieldLedger will be designed to support will almost always include multivariate methods that I learned about in this class. While I am not using them directly for my thesis project, they have also cemeted the importance of avoidnig missing data, helped me see how datasets with different datatypes are analyzed together, and therefore informed how I have to store much of the quantitative data that FieldLedger uses. Understanding how my data will be used is crucial for understanding the best way to store it, and to return it when it is queried by researchers.

NRES 420 was originally a class that I took mostly out of personal interest, and it ended up being one of my personal favorites. I think that the main skill I learned here was how to read a researech paper and understand it and answer questions about it from the perspective of the author, rather than through the lens of my own experience. Unexpectedly, this helped me a lot while working on FieldLedger, as I was able to apply this to my interviews with stakeholders to understand how they would actually use it rather than how I interpreted their needs by comparing them to how I thought they would use it. The restoration projects that we looked at in this class also really helped me understand how quantitative data is collected in biological systems, and why that data is so difficult to collect in a way that is scientifically rigorous.

### 2026.06 Jun

### 2026.07 Jul

### 2026.08 Aug

I have worked on the sync protocol and interface, trying to get it to a place that I can show stakeholders and ask for their opinions on the most important next steps for FieldLedger.

This time has also been very busy in putting together slideshows for various presentations of this project, a poster, a thesis abstract, and more. This includes generating examples and fairly extensive documentation.
